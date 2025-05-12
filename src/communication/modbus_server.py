"""
Modbus RTU server for exposing radar data to ThingsBoard Gateway.
"""
import threading
import time
import yaml
from typing import Dict, List, Optional, Any

from loguru import logger
from pymodbus.server import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

from src.simulators.radar_simulator import RadarSimulator


class ModbusServer:
    """
    Modbus RTU server for exposing radar data to ThingsBoard Gateway.
    
    Attributes:
        radar_simulator (RadarSimulator): Radar simulator instance
        config (Dict): Modbus configuration
        server_thread (threading.Thread): Thread running the Modbus server
        running (bool): Server running status
        context (ModbusServerContext): Modbus server context
        slave_context (ModbusSlaveContext): Modbus slave context
    """
    
    def __init__(self, radar_simulator: RadarSimulator, config_path: str):
        """
        Initialize the Modbus server.
        
        Args:
            radar_simulator: Radar simulator instance
            config_path: Path to the communication configuration file
        """
        self.radar_simulator = radar_simulator
        self.config = self._load_config(config_path)
        self.server_thread = None
        self.running = False
        self.context = None
        self.slave_context = None
        self.server = None
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _create_context(self) -> ModbusServerContext:
        """
        Create the Modbus server context with initial register values.
        
        Returns:
            Modbus server context
        """
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        
        # Create a data block large enough for all radars
        # Each radar has a block of registers_per_tank registers
        # The first register is at tank_base_address
        max_address = len(self.radar_simulator.radars)
        block_size = tank_base_address + (max_address * registers_per_tank) + 100  # Extra space
        
        # Create data blocks for different register types
        # We'll use holding registers for all data in this example
        hr_block = ModbusSequentialDataBlock(0, [0] * block_size)
        
        # Create slave context
        self.slave_context = ModbusSlaveContext(
            hr=hr_block,
            ir=ModbusSequentialDataBlock(0, [0] * block_size),
            co=ModbusSequentialDataBlock(0, [0] * block_size),
            di=ModbusSequentialDataBlock(0, [0] * block_size)
        )
        
        # Create server context with a single slave
        slave_id = self.config['modbus']['server']['unit_id']
        context = ModbusServerContext(slaves={slave_id: self.slave_context}, single=False)
        
        return context
    
    def _update_registers(self) -> None:
        """Update Modbus registers with current radar data."""
        # Get current register values from radar simulator
        radar_registers = self.radar_simulator.get_modbus_registers()
        
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        offsets = register_config['offsets']
        
        # Verificamos si tenemos acceso al contexto de esclavo
        if not hasattr(self, 'slave_context') or self.slave_context is None:
            logger.error("Modbus slave context not initialized")
            return
            
        try:
            # Update registers for each radar
            for modbus_address, registers in radar_registers.items():
                # Calculate base address for this radar
                base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
                
                # Update each register
                for register_name, value in registers.items():
                    if register_name in offsets:
                        # Calculate register address
                        address = base_address + offsets[register_name]
                        
                        # Get data type for this register
                        data_type = self.config['modbus']['data_types'].get(
                            register_name.split('_')[0], 'uint16'
                        )
                        
                        # Write value to register
                        if data_type == 'uint32':
                            # 32-bit value requires two registers
                            # Write high word to first register, low word to second
                            high_word = (value >> 16) & 0xFFFF
                            low_word = value & 0xFFFF
                            
                            # Escribir en los registros holding (tipo 3)
                            self.slave_context.setValues(3, address, [high_word, low_word])
                        elif data_type == 'int16':
                            # Convert to 16-bit signed integer
                            if value < 0:
                                value = 65536 + value
                                
                            # Escribir en los registros holding (tipo 3)
                            self.slave_context.setValues(3, address, [value & 0xFFFF])
                        else:  # uint16
                            # Escribir en los registros holding (tipo 3)
                            self.slave_context.setValues(3, address, [value & 0xFFFF])
        except Exception as e:
            logger.error(f"Error updating registers: {e}")
    
    def _check_register_writes(self) -> None:
        """Check for register writes and update radar configuration."""
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        offsets = register_config['offsets']
        
        # Verificamos si tenemos acceso al contexto de esclavo
        if not hasattr(self, 'slave_context') or self.slave_context is None:
            logger.error("Modbus slave context not initialized")
            return
            
        try:
            # Check writable registers for each radar
            writable_registers = ['radar_height', 'fine_adjustment']
            
            for modbus_address in range(1, len(self.radar_simulator.radars) + 1):
                # Calculate base address for this radar
                base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
                
                # Check each writable register
                for register_name in writable_registers:
                    if register_name in offsets:
                        # Calculate register address
                        address = base_address + offsets[register_name]
                        
                        # Get data type for this register
                        data_type = self.config['modbus']['data_types'].get(
                            register_name.split('_')[0], 'uint16'
                        )
                        
                        # Read current value
                        try:
                            if data_type == 'uint32':
                                # 32-bit value requires two registers
                                values = self.slave_context.getValues(3, address, 2)
                                value = (values[0] << 16) | values[1]
                            else:  # uint16 or int16
                                values = self.slave_context.getValues(3, address, 1)
                                value = values[0]
                                
                            # Convert from 16-bit signed integer if needed
                            if data_type == 'int16' and value > 32767:
                                value = value - 65536
                            
                            # Update radar configuration if value has changed
                            self.radar_simulator.update_radar_configuration(
                                modbus_address, register_name, value
                            )
                        except Exception as e:
                            logger.error(f"Error reading register {register_name}: {e}")
        except Exception as e:
            logger.error(f"Error checking register writes: {e}")
    
    def _server_loop(self) -> None:
        """Main server loop for updating registers."""
        while self.running:
            # Update registers with current radar data
            self._update_registers()
            
            # Check for register writes
            self._check_register_writes()
            
            # Sleep for a short time
            time.sleep(0.1)
    
    def start(self) -> bool:
        """
        Start the Modbus server.
        
        Returns:
            True if server was started successfully, False otherwise
        """
        if self.running:
            logger.warning("Modbus server already running")
            return True
        
        try:
            # Create server context
            self.context = self._create_context()
            
            # Get RTU port settings
            port_settings = {
                'port': self.config['modbus']['server']['port'],
                'baudrate': self.config['modbus']['server']['baudrate'],
                'bytesize': self.config['modbus']['server']['bytesize'],
                'parity': self.config['modbus']['server']['parity'],
                'stopbits': self.config['modbus']['server']['stopbits'],
                'timeout': self.config['modbus']['server']['timeout']
            }
            
            logger.info(f"Starting Modbus RTU server on {port_settings['port']} at {port_settings['baudrate']} baud")
            
            # Start server thread for updating registers
            self.running = True
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Start the RTU server in a separate thread
            server_thread = threading.Thread(
                target=self._start_rtu_server,
                args=(port_settings,)
            )
            server_thread.daemon = True
            server_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting Modbus server: {e}")
            self.running = False
            return False
    
    def _start_rtu_server(self, port_settings) -> None:
        """Start the Modbus RTU server over serial port."""
        try:
            # Crear la identidad del dispositivo Modbus
            identity = ModbusDeviceIdentification()
            identity.VendorName = 'SAAB Radar Simulator'
            identity.ProductCode = 'SAAB-RTU'
            identity.VendorUrl = 'https://www.saab.com/'
            identity.ProductName = 'SAAB Tank Radar'
            identity.ModelName = 'RTG 3900'
            identity.MajorMinorRevision = '1.0'
            
            # En pymodbus 3.9.2, StartSerialServer inicia el servidor y bloquea el hilo
            # Por lo que debemos ejecutarlo en un hilo separado
            self.server_thread = threading.Thread(
                target=self._run_rtu_server,
                args=(port_settings, identity)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"Modbus RTU server thread started")
        except Exception as e:
            logger.error(f"Error starting RTU server thread: {e}")
            
    def _run_rtu_server(self, port_settings, identity) -> None:
        """Run the Modbus RTU server in a separate thread."""
        try:
            # Iniciar el servidor RTU
            self.server = StartSerialServer(
                context=self.context,
                identity=identity,
                port=port_settings['port'],
                baudrate=port_settings['baudrate'],
                bytesize=port_settings['bytesize'],
                parity=port_settings['parity'],
                stopbits=port_settings['stopbits'],
                timeout=port_settings['timeout']
            )
            # StartSerialServer bloquea este hilo hasta que se detenga el servidor
        except Exception as e:
            logger.error(f"Error in RTU server: {e}")
    
    def stop(self) -> None:
        """Stop the Modbus server."""
        self.running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
        
        # Stop the server if it's running
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()
    
    def generate_thingsboard_gateway_config(self) -> Dict:
        """
        Generate ThingsBoard Gateway configuration for Modbus extension.
        
        Returns:
            Configuration dictionary for ThingsBoard Gateway
        """
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        offsets = register_config['offsets']
        
        # Create configuration
        gateway_config = {
            "server": {
                "name": "Refinery Tank Simulator",
                "type": "serial",
                "port": self.config['modbus']['server']['port'],
                "baudrate": self.config['modbus']['server']['baudrate'],
                "bytesize": self.config['modbus']['server']['bytesize'],
                "parity": self.config['modbus']['server']['parity'],
                "stopbits": self.config['modbus']['server']['stopbits'],
                "timeout": self.config['modbus']['server']['timeout'],
                "method": "rtu"
            },
            "slave": {
                "slaves": [
                    {
                        "id": self.config['modbus']['server']['unit_id'],
                        "name": "TankRadars",
                        "deviceType": "SAAB Radar",
                        "pollPeriod": 5000,
                        "attributes": [],
                        "timeseries": []
                    }
                ]
            }
        }
        
        # Add registers for each radar
        slave = gateway_config["slave"]["slaves"][0]
        
        for modbus_address in range(1, len(self.radar_simulator.radars) + 1):
            # Calculate base address for this radar
            base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
            
            # Add each register
            for register_name, offset in offsets.items():
                # Calculate register address
                address = base_address + offset
                
                # Get data type for this register
                data_type = self.config['modbus']['data_types'].get(
                    register_name.split('_')[0], 'uint16'
                )
                
                # Create register configuration
                register_config = {
                    "tag": f"radar{modbus_address}_{register_name}",
                    "type": "holding",
                    "address": address,
                    "registerCount": 2 if data_type == 'uint32' else 1,
                    "byteOrder": "BIG",
                    "wordOrder": "BIG",
                    "functionCode": 3
                }
                
                # Add to appropriate section
                if register_name in ['radar_height', 'fine_adjustment']:
                    slave["attributes"].append(register_config)
                else:
                    slave["timeseries"].append(register_config)
        
        return gateway_config
