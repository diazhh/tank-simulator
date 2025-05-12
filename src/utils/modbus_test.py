"""
Utility module for testing Modbus RTU communication with ThingsBoard Gateway.
"""
import os
import sys
import time
import argparse
from typing import Dict, List, Optional

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config_loader import ConfigLoader


class ModbusTest:
    """
    Class for testing Modbus RTU communication with the simulator.
    
    Attributes:
        client (ModbusTcpClient): Modbus TCP client
        config (Dict): Communication configuration
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Modbus test client.
        
        Args:
            config_path: Path to the communication configuration file
        """
        # Load configuration
        config_loader = ConfigLoader(os.path.dirname(config_path))
        self.config = config_loader.load_config(os.path.basename(config_path).split('.')[0])
        
        # Create Modbus client
        self.client = ModbusTcpClient(
            host=self.config['modbus']['server']['host'],
            port=self.config['modbus']['server']['port']
        )
    
    def connect(self) -> bool:
        """
        Connect to the Modbus server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        return self.client.connect()
    
    def disconnect(self) -> None:
        """Disconnect from the Modbus server."""
        self.client.close()
    
    def read_radar_data(self, modbus_address: int) -> Dict:
        """
        Read radar data from the Modbus server.
        
        Args:
            modbus_address: Modbus address of the radar
            
        Returns:
            Dictionary containing radar data
        """
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        offsets = register_config['offsets']
        
        # Calculate base address for this radar
        base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
        
        # Create result dictionary
        result = {}
        
        # Read each register
        for register_name, offset in offsets.items():
            # Calculate register address
            address = base_address + offset
            
            # Get data type for this register
            data_type = self.config['modbus']['data_types'].get(
                register_name.split('_')[0], 'uint16'
            )
            
            # Read register
            if data_type == 'uint32':
                # 32-bit value requires two registers
                response = self.client.read_holding_registers(
                    address=address,
                    count=2,
                    unit=self.config['modbus']['server']['unit_id']
                )
                
                if response.isError():
                    print(f"Error reading register {register_name}: {response}")
                    result[register_name] = None
                else:
                    # Decode 32-bit value
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        response.registers,
                        byteorder=Endian.Big,
                        wordorder=Endian.Big
                    )
                    value = decoder.decode_32bit_uint()
                    result[register_name] = value
            else:  # uint16 or int16
                response = self.client.read_holding_registers(
                    address=address,
                    count=1,
                    unit=self.config['modbus']['server']['unit_id']
                )
                
                if response.isError():
                    print(f"Error reading register {register_name}: {response}")
                    result[register_name] = None
                else:
                    value = response.registers[0]
                    
                    # Convert from 16-bit signed integer if needed
                    if data_type == 'int16' and value > 32767:
                        value = value - 65536
                    
                    # Apply scaling for specific registers
                    if register_name.startswith('temperature'):
                        value = value / 10.0  # Scale by 0.1
                    elif register_name == 'pressure':
                        value = value / 100.0  # Scale by 0.01
                    elif register_name == 'fine_adjustment':
                        value = value / 10.0  # Scale by 0.1
                    
                    result[register_name] = value
        
        return result
    
    def write_radar_config(self, modbus_address: int, register_name: str, value: int) -> bool:
        """
        Write radar configuration to the Modbus server.
        
        Args:
            modbus_address: Modbus address of the radar
            register_name: Name of the register to write
            value: Value to write
            
        Returns:
            True if write was successful, False otherwise
        """
        # Check if register is writable
        if register_name not in ['radar_height', 'fine_adjustment']:
            print(f"Error: Register {register_name} is not writable")
            return False
        
        # Get register configuration
        register_config = self.config['modbus']['registers']
        tank_base_address = register_config['tank_base_address']
        registers_per_tank = self.config['modbus']['registers_per_tank']
        offsets = register_config['offsets']
        
        # Calculate base address for this radar
        base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
        
        # Calculate register address
        address = base_address + offsets[register_name]
        
        # Get data type for this register
        data_type = self.config['modbus']['data_types'].get(
            register_name.split('_')[0], 'uint16'
        )
        
        # Write register
        if data_type == 'uint32':
            # 32-bit value requires two registers
            # Write high word to first register, low word to second
            high_word = (value >> 16) & 0xFFFF
            low_word = value & 0xFFFF
            
            response = self.client.write_registers(
                address=address,
                values=[high_word, low_word],
                unit=self.config['modbus']['server']['unit_id']
            )
        else:  # uint16 or int16
            # Apply scaling for specific registers
            if register_name == 'fine_adjustment':
                value = int(value * 10)  # Scale by 10
            
            # Convert to 16-bit signed integer if needed
            if data_type == 'int16' and value < 0:
                value = 65536 + value
            
            response = self.client.write_register(
                address=address,
                value=value,
                unit=self.config['modbus']['server']['unit_id']
            )
        
        if response.isError():
            print(f"Error writing register {register_name}: {response}")
            return False
        
        return True


def main():
    """Main entry point for Modbus test utility."""
    parser = argparse.ArgumentParser(description='Modbus Test Utility')
    parser.add_argument('--config', type=str, default='../config/communication.yaml',
                        help='Path to communication configuration file')
    parser.add_argument('--action', type=str, choices=['read', 'write'], required=True,
                        help='Action to perform')
    parser.add_argument('--address', type=int, required=True,
                        help='Modbus address of the radar')
    parser.add_argument('--register', type=str,
                        help='Register name (required for write action)')
    parser.add_argument('--value', type=int,
                        help='Value to write (required for write action)')
    parser.add_argument('--monitor', action='store_true',
                        help='Continuously monitor radar data')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Monitoring interval in seconds')
    args = parser.parse_args()
    
    # Create Modbus test client
    test_client = ModbusTest(args.config)
    
    # Connect to server
    print(f"Connecting to Modbus server at {test_client.config['modbus']['server']['host']}:{test_client.config['modbus']['server']['port']}...")
    if not test_client.connect():
        print("Error: Failed to connect to Modbus server")
        sys.exit(1)
    
    try:
        if args.action == 'read':
            if args.monitor:
                # Continuously monitor radar data
                print(f"Monitoring radar at address {args.address} (Ctrl+C to stop)...")
                try:
                    while True:
                        data = test_client.read_radar_data(args.address)
                        print("\033c", end="")  # Clear terminal
                        print(f"Radar {args.address} Data:")
                        print("-" * 40)
                        for name, value in data.items():
                            print(f"{name}: {value}")
                        print("-" * 40)
                        time.sleep(args.interval)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped")
            else:
                # Read radar data once
                data = test_client.read_radar_data(args.address)
                print(f"Radar {args.address} Data:")
                print("-" * 40)
                for name, value in data.items():
                    print(f"{name}: {value}")
                print("-" * 40)
        
        elif args.action == 'write':
            # Check required arguments
            if not args.register:
                print("Error: Register name is required for write action")
                sys.exit(1)
            
            if args.value is None:
                print("Error: Value is required for write action")
                sys.exit(1)
            
            # Write radar configuration
            print(f"Writing {args.value} to register {args.register} of radar {args.address}...")
            if test_client.write_radar_config(args.address, args.register, args.value):
                print("Write successful")
                
                # Read back the value to confirm
                data = test_client.read_radar_data(args.address)
                print(f"New value: {data[args.register]}")
            else:
                print("Write failed")
    
    finally:
        # Disconnect from server
        test_client.disconnect()


if __name__ == '__main__':
    main()
