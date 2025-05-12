"""
Modbus RTU client compatible with pymodbus 3.9.2.
"""
import time
import yaml
import argparse
from loguru import logger

from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

def run_client(monitor=False, address=1, interval=1.0):
    """Run a Modbus RTU client compatible with pymodbus 3.9.2."""
    # Load configuration
    with open('/var/new-tank-simulator/config/communication.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Create Modbus RTU client - using the second port of the virtual serial pair
    # If the server is using /tmp/ttyS10, we use /tmp/ttyS11
    client_port = "/tmp/ttyS11"  # Cliente usa el otro extremo del puerto virtual
    
    # En pymodbus 3.9.2, la forma de crear un cliente ha cambiado
    client = ModbusSerialClient(
        port=client_port,
        baudrate=config['modbus']['server']['baudrate'],
        bytesize=config['modbus']['server']['bytesize'],
        parity=config['modbus']['server']['parity'],
        stopbits=config['modbus']['server']['stopbits'],
        timeout=config['modbus']['server']['timeout']
    )
    
    logger.info(f"Connecting to Modbus RTU server via {client_port}...")
    
    # Connect to the server
    if not client.connect():
        logger.error("Failed to connect to the server")
        return
    
    logger.info("Connected to the server")
    
    # Read holding registers
    try:
        if monitor:
            logger.info(f"Monitoring Modbus address {address} every {interval} seconds. Press Ctrl+C to stop.")
            while True:
                # Read the first 10 registers
                # En pymodbus 3.9.2, el parámetro slave se pasa como slave= (keyword argument)
                response = client.read_holding_registers(0, 10, slave=config['modbus']['server']['unit_id'])
                
                if response.isError():
                    logger.error(f"Error reading registers: {response}")
                else:
                    logger.info(f"Registers: {response.registers}")
                
                time.sleep(interval)
        else:
            # Read the first 10 registers once
            # En pymodbus 3.9.2, el parámetro slave se pasa como slave= (keyword argument)
            response = client.read_holding_registers(0, 10, slave=config['modbus']['server']['unit_id'])
            
            if response.isError():
                logger.error(f"Error reading registers: {response}")
            else:
                logger.info(f"Registers: {response.registers}")
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        client.close()
        logger.info("Connection closed")

def main():
    """Main entry point for Modbus RTU client."""
    parser = argparse.ArgumentParser(description="Modbus RTU Client")
    parser.add_argument("--monitor", action="store_true", help="Continuously monitor data")
    parser.add_argument("--address", type=int, default=1, help="Modbus address to read")
    parser.add_argument("--interval", type=float, default=1.0, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    run_client(
        monitor=args.monitor,
        address=args.address,
        interval=args.interval
    )

if __name__ == "__main__":
    main()
