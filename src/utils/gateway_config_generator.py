"""
Utility module for generating ThingsBoard Gateway configuration files.
"""
import os
import sys
import json
import argparse
from typing import Dict, List, Optional

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config_loader import ConfigLoader
from src.models.factory import TankFactory


def generate_modbus_config(config_path: str, output_path: str):
    """
    Generate Modbus configuration for ThingsBoard Gateway.
    
    Args:
        config_path: Path to the communication configuration file
        output_path: Path to save the generated configuration
    """
    # Load configuration
    config_loader = ConfigLoader(os.path.dirname(config_path))
    config = config_loader.load_config(os.path.basename(config_path).split('.')[0])
    
    # Create tanks and radars to get the correct number of devices
    tanks_config_path = os.path.join(os.path.dirname(config_path), "tanks.yaml")
    tank_factory = TankFactory(tanks_config_path)
    tanks, radars = tank_factory.create_tanks_and_radars()
    
    # Get register configuration
    register_config = config['modbus']['registers']
    tank_base_address = register_config['tank_base_address']
    registers_per_tank = config['modbus']['registers_per_tank']
    offsets = register_config['offsets']
    
    # Create configuration
    modbus_config = {
        "server": {
            "name": "Refinery Tank Simulator",
            "type": "tcp",
            "host": config['modbus']['server']['host'],
            "port": config['modbus']['server']['port'],
            "timeout": 35,
            "reconnect": True,
            "rtu": False
        },
        "slave": {
            "slaves": [
                {
                    "id": config['modbus']['server']['unit_id'],
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
    slave = modbus_config["slave"]["slaves"][0]
    
    for modbus_address in range(1, len(radars) + 1):
        # Get tank and radar
        radar = next((r for r in radars if r.modbus_address == modbus_address), None)
        if not radar:
            continue
        
        tank = next((t for t in tanks if t.id == radar.tank_id), None)
        if not tank:
            continue
        
        # Calculate base address for this radar
        base_address = tank_base_address + ((modbus_address - 1) * registers_per_tank)
        
        # Add each register
        for register_name, offset in offsets.items():
            # Calculate register address
            address = base_address + offset
            
            # Get data type for this register
            data_type = config['modbus']['data_types'].get(
                register_name.split('_')[0], 'uint16'
            )
            
            # Create register configuration
            register_config = {
                "tag": f"{tank.id}_{register_name}",
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
    
    # Save configuration to file
    with open(output_path, 'w') as file:
        json.dump(modbus_config, file, indent=2)
    
    print(f"Generated Modbus configuration for {len(radars)} radars")
    print(f"Configuration saved to {output_path}")


def generate_mqtt_config(config_path: str, output_path: str):
    """
    Generate MQTT configuration for ThingsBoard Gateway.
    
    Args:
        config_path: Path to the communication configuration file
        output_path: Path to save the generated configuration
    """
    # Load configuration
    config_loader = ConfigLoader(os.path.dirname(config_path))
    config = config_loader.load_config(os.path.basename(config_path).split('.')[0])
    
    # Create MQTT configuration
    mqtt_config = {
        "broker": {
            "name": "Refinery Tank Simulator MQTT Broker",
            "host": config['mqtt']['broker'],
            "port": config['mqtt']['port'],
            "security": {
                "type": "basic",
                "username": config['mqtt'].get('username', ''),
                "password": config['mqtt'].get('password', '')
            }
        },
        "mapping": [
            {
                "topicFilter": config['mqtt']['thingsboard']['base_topic'] + "/#",
                "converter": {
                    "type": "json",
                    "deviceNameJsonExpression": "${$.id}",
                    "deviceTypeJsonExpression": "Tank",
                    "attributes": [
                        {
                            "key": "id",
                            "type": "string",
                            "value": "${$.id}"
                        },
                        {
                            "key": "patio",
                            "type": "string",
                            "value": "${$.patio}"
                        },
                        {
                            "key": "product",
                            "type": "string",
                            "value": "${$.product}"
                        },
                        {
                            "key": "height",
                            "type": "double",
                            "value": "${$.height}"
                        },
                        {
                            "key": "diameter",
                            "type": "double",
                            "value": "${$.diameter}"
                        },
                        {
                            "key": "capacity",
                            "type": "double",
                            "value": "${$.capacity}"
                        },
                        {
                            "key": "tank_type",
                            "type": "string",
                            "value": "${$.tank_type}"
                        },
                        {
                            "key": "strapping_table",
                            "type": "json",
                            "value": "${$.strapping_table}"
                        }
                    ],
                    "timeseries": [
                        {
                            "key": "level",
                            "type": "double",
                            "value": "${$.level}"
                        },
                        {
                            "key": "volume",
                            "type": "double",
                            "value": "${$.volume}"
                        },
                        {
                            "key": "fill_percentage",
                            "type": "double",
                            "value": "${$.fill_percentage}"
                        },
                        {
                            "key": "state",
                            "type": "string",
                            "value": "${$.state}"
                        },
                        {
                            "key": "temperatures",
                            "type": "json",
                            "value": "${$.temperatures}"
                        },
                        {
                            "key": "average_temperature",
                            "type": "double",
                            "value": "${$.average_temperature}"
                        },
                        {
                            "key": "pressure",
                            "type": "double",
                            "value": "${$.pressure}"
                        }
                    ]
                }
            }
        ]
    }
    
    # Save configuration to file
    with open(output_path, 'w') as file:
        json.dump(mqtt_config, file, indent=2)
    
    print(f"Generated MQTT configuration")
    print(f"Configuration saved to {output_path}")


def main():
    """Main entry point for gateway configuration generator utility."""
    parser = argparse.ArgumentParser(description='ThingsBoard Gateway Configuration Generator')
    parser.add_argument('--config', type=str, default='../config/communication.yaml',
                        help='Path to communication configuration file')
    parser.add_argument('--output-dir', type=str, default='../thingsboard_gateway',
                        help='Directory to save generated configurations')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate Modbus configuration
    modbus_output_path = os.path.join(args.output_dir, 'modbus_mapping.json')
    generate_modbus_config(args.config, modbus_output_path)
    
    # Generate MQTT configuration
    mqtt_output_path = os.path.join(args.output_dir, 'mqtt_mapping.json')
    generate_mqtt_config(args.config, mqtt_output_path)


if __name__ == '__main__':
    main()
