"""
Modbus RTU server compatible with pymodbus 3.9.2.
"""
import time
import yaml
import threading
from loguru import logger

from pymodbus.server import StartSerialServer, ModbusSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock

def run_server():
    """Run a Modbus RTU server compatible with pymodbus 3.9.2."""
    # Load configuration
    with open('/var/new-tank-simulator/config/communication.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Create data blocks
    block_size = 1000  # Tamaño suficiente para todos los registros
    
    # Create slave context
    slave_context = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * block_size),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0] * block_size),  # Coils
        hr=ModbusSequentialDataBlock(0, [0] * block_size),  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0] * block_size)   # Input Registers
    )
    
    # Create server context
    slave_id = config['modbus']['server']['unit_id']
    server_context = ModbusServerContext(slaves={slave_id: slave_context}, single=False)
    
    # Set some test values in holding registers
    for i in range(10):
        slave_context.setValues(3, i, [i * 100])
    
    # Get RTU port settings
    port_settings = {
        'port': config['modbus']['server']['port'],
        'baudrate': config['modbus']['server']['baudrate'],
        'bytesize': config['modbus']['server']['bytesize'],
        'parity': config['modbus']['server']['parity'],
        'stopbits': config['modbus']['server']['stopbits'],
        'timeout': config['modbus']['server']['timeout']
    }
    
    logger.info(f"Starting Modbus RTU server on {port_settings['port']} at {port_settings['baudrate']} baud")
    
    # Start the server
    try:
        # En pymodbus 3.9.2, usamos StartSerialServer para servidores síncronos
        server = StartSerialServer(
            context=server_context,
            **port_settings
        )
        # StartSerialServer ya inicia el servidor y bloquea el hilo
    except Exception as e:
        logger.error(f"Error starting RTU server: {e}")

if __name__ == "__main__":
    run_server()
