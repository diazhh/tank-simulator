"""
Simple Modbus RTU client for testing with pymodbus 3.9.2.
"""
import time
from loguru import logger
from pymodbus.client import ModbusSerialClient

def main():
    """Run a simple Modbus RTU client."""
    # Create Modbus RTU client
    client = ModbusSerialClient(
        port="/tmp/ttyS11",
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )
    
    logger.info("Connecting to Modbus RTU server...")
    
    # Connect to the server
    if not client.connect():
        logger.error("Failed to connect to the server")
        return
    
    logger.info("Connected to the server")
    
    try:
        # Read holding registers - address, count
        response = client.read_holding_registers(address=0, count=10)
        
        if hasattr(response, 'isError') and response.isError():
            logger.error(f"Error reading registers: {response}")
        else:
            logger.info(f"Registers: {response.registers}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        client.close()
        logger.info("Connection closed")

if __name__ == "__main__":
    main()
