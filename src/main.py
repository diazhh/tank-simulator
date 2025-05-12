"""
Main module for the refinery tank simulator.
"""
import os
import sys
import time
import signal
import argparse
import json
from typing import Dict, List

from loguru import logger

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.factory import TankFactory
from src.simulators.tank_simulator import TankSimulator
from src.simulators.radar_simulator import RadarSimulator
from src.communication.mqtt_client import MQTTClient
from src.communication.modbus_server import ModbusServer
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger


class TankSimulatorApp:
    """
    Main application class for the refinery tank simulator.
    
    Attributes:
        config_loader (ConfigLoader): Configuration loader
        tanks (List[Tank]): List of tanks
        radars (List[Radar]): List of radars
        tank_simulator (TankSimulator): Tank simulator
        radar_simulator (RadarSimulator): Radar simulator
        mqtt_client (MQTTClient): MQTT client
        modbus_server (ModbusServer): Modbus server
        running (bool): Application running status
    """
    
    def __init__(self, config_dir: str):
        """
        Initialize the application.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_loader = ConfigLoader(config_dir)
        self.tanks = []
        self.radars = []
        self.tank_simulator = None
        self.radar_simulator = None
        self.mqtt_client = None
        self.modbus_server = None
        self.running = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle signals to gracefully shutdown."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        Initialize the application components.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Load configurations
            logger.info("Loading configurations...")
            simulation_config = self.config_loader.load_config("simulation")
            tanks_config = self.config_loader.load_config("tanks")
            communication_config = self.config_loader.load_config("communication")
            
            # Validate configurations
            if not self.config_loader.validate_simulation_config(simulation_config):
                logger.error("Invalid simulation configuration")
                return False
            
            if not self.config_loader.validate_tanks_config(tanks_config):
                logger.error("Invalid tanks configuration")
                return False
            
            if not self.config_loader.validate_communication_config(communication_config):
                logger.error("Invalid communication configuration")
                return False
            
            # Set up logger
            setup_logger(simulation_config)
            
            # Create tanks and radars
            logger.info("Creating tanks and radars...")
            tank_factory = TankFactory(os.path.join(self.config_loader.config_dir, "tanks.yaml"))
            self.tanks, self.radars = tank_factory.create_tanks_and_radars()
            
            logger.info(f"Created {len(self.tanks)} tanks and {len(self.radars)} radars")
            
            # Create simulators
            logger.info("Creating simulators...")
            self.tank_simulator = TankSimulator(
                self.tanks,
                os.path.join(self.config_loader.config_dir, "simulation.yaml")
            )
            
            self.radar_simulator = RadarSimulator(
                self.radars,
                self.tanks,
                os.path.join(self.config_loader.config_dir, "simulation.yaml")
            )
            
            # Create communication components
            logger.info("Creating communication components...")
            self.mqtt_client = MQTTClient(
                self.tanks,
                os.path.join(self.config_loader.config_dir, "communication.yaml")
            )
            
            self.modbus_server = ModbusServer(
                self.radar_simulator,
                os.path.join(self.config_loader.config_dir, "communication.yaml")
            )
            
            # Generate ThingsBoard Gateway configuration
            self._generate_thingsboard_gateway_config()
            
            return True
        except Exception as e:
            logger.exception(f"Error initializing application: {e}")
            return False
    
    def _generate_thingsboard_gateway_config(self) -> None:
        """Generate ThingsBoard Gateway configuration files."""
        # Create directory for ThingsBoard Gateway configuration
        gateway_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'thingsboard_gateway')
        os.makedirs(gateway_dir, exist_ok=True)
        
        # Generate Modbus mapping
        modbus_config = self.modbus_server.generate_thingsboard_gateway_config()
        modbus_config_path = os.path.join(gateway_dir, 'modbus_mapping.json')
        
        with open(modbus_config_path, 'w') as file:
            json.dump(modbus_config, file, indent=2)
        
        logger.info(f"Generated ThingsBoard Gateway Modbus configuration: {modbus_config_path}")
        
        # Generate MQTT mapping
        mqtt_config = {
            "broker": {
                "name": "Refinery Tank Simulator MQTT Broker",
                "host": self.mqtt_client.config['mqtt']['broker'],
                "port": self.mqtt_client.config['mqtt']['port'],
                "security": {
                    "type": "basic",
                    "username": self.mqtt_client.config['mqtt'].get('username', ''),
                    "password": self.mqtt_client.config['mqtt'].get('password', '')
                }
            },
            "mapping": [
                {
                    "topicFilter": self.mqtt_client.config['mqtt']['thingsboard']['base_topic'] + "/#",
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
        
        mqtt_config_path = os.path.join(gateway_dir, 'mqtt_mapping.json')
        
        with open(mqtt_config_path, 'w') as file:
            json.dump(mqtt_config, file, indent=2)
        
        logger.info(f"Generated ThingsBoard Gateway MQTT configuration: {mqtt_config_path}")
    
    def start(self) -> bool:
        """
        Start the application.
        
        Returns:
            True if application was started successfully, False otherwise
        """
        if self.running:
            logger.warning("Application already running")
            return True
        
        try:
            # Inicializar MQTT y enviar los assets (patios y tanques) una sola vez
            mqtt_enabled = self.mqtt_client.config['mqtt'].get('enabled', True)
            if mqtt_enabled:
                logger.info("Initializing MQTT and publishing assets...")
                if not self.mqtt_client.initialize_mqtt():
                    logger.warning("Failed to initialize MQTT, continuing without MQTT")
            else:
                logger.info("MQTT disabled in configuration, continuing without MQTT")
            
            # Start Modbus server
            logger.info("Starting Modbus server...")
            if not self.modbus_server.start():
                logger.error("Failed to start Modbus server")
                return False
            
            # Start main loop
            self.running = True
            logger.info("Application started")
            
            return True
        except Exception as e:
            logger.exception(f"Error starting application: {e}")
            return False
    
    def run(self) -> None:
        """Run the application main loop."""
        if not self.running:
            logger.error("Application not started")
            return
        
        # Get update interval from config
        simulation_config = self.config_loader.load_config("simulation")
        update_interval = simulation_config.get('simulation', {}).get('update_interval', 60)
        
        logger.info(f"Running with update interval of {update_interval} seconds")
        
        try:
            while self.running:
                start_time = time.time()
                
                # Update tank simulator
                self.tank_simulator.update()
                
                # Update radar simulator
                self.radar_simulator.update()
                
                # No es necesario actualizar el cliente MQTT ya que solo enviamos los assets una vez al inicio
                # self.mqtt_client.update()
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0.1, update_interval - elapsed)
                
                # Log status periodically
                logger.debug(f"Update completed in {elapsed:.2f} seconds, sleeping for {sleep_time:.2f} seconds")
                
                # Sleep until next update
                time.sleep(sleep_time)
        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the application."""
        if not self.running:
            return
        
        logger.info("Stopping application...")
        
        # Stop components
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        if self.modbus_server:
            self.modbus_server.stop()
        
        self.running = False
        logger.info("Application stopped")


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Refinery Tank Simulator')
    parser.add_argument('--config-dir', type=str, default='../config',
                        help='Directory containing configuration files')
    args = parser.parse_args()
    
    # Resolve config directory path
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.config_dir))
    
    # Create and run application
    app = TankSimulatorApp(config_dir)
    
    if app.initialize():
        if app.start():
            app.run()
    else:
        logger.error("Failed to initialize application")
        sys.exit(1)


if __name__ == '__main__':
    main()
