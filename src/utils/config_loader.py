"""
Utility module for loading and validating configuration.
"""
import os
from typing import Dict

import yaml
from loguru import logger


class ConfigLoader:
    """
    Class for loading and validating configuration files.
    
    Attributes:
        config_dir (str): Directory containing configuration files
    """
    
    def __init__(self, config_dir: str):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
    
    def load_config(self, config_name: str) -> Dict:
        """
        Load a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            
        Returns:
            Configuration dictionary
        
        Raises:
            FileNotFoundError: If the configuration file does not exist
            ValueError: If the configuration file is invalid
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            return config
        except Exception as e:
            raise ValueError(f"Error loading configuration file {config_path}: {e}")
    
    def validate_simulation_config(self, config: Dict) -> bool:
        """
        Validate simulation configuration.
        
        Args:
            config: Simulation configuration dictionary
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required sections
        required_sections = ['simulation', 'environment', 'operations', 'radar']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required section in simulation config: {section}")
                return False
        
        # Check operation parameters
        if 'operations' in config:
            if 'flow_rates' not in config['operations']:
                logger.error("Missing flow_rates in operations section")
                return False
            
            if 'temperature_ranges' not in config['operations']:
                logger.error("Missing temperature_ranges in operations section")
                return False
            
            # Check products in flow_rates and temperature_ranges
            products = ['crudo', 'gasolina', 'diesel', 'fuel_jet', 'asfalto']
            for product in products:
                if product not in config['operations']['flow_rates']:
                    logger.error(f"Missing product {product} in flow_rates")
                    return False
                
                if product not in config['operations']['temperature_ranges']:
                    logger.error(f"Missing product {product} in temperature_ranges")
                    return False
        
        return True
    
    def validate_tanks_config(self, config: Dict) -> bool:
        """
        Validate tanks configuration.
        
        Args:
            config: Tanks configuration dictionary
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required sections
        required_sections = ['patios', 'tank_size_ranges', 'product_distribution', 'tank_types']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required section in tanks config: {section}")
                return False
        
        # Check patios
        if 'patios' in config:
            total_tanks = 0
            for patio in config['patios']:
                if 'name' not in patio or 'prefix' not in patio or 'count' not in patio:
                    logger.error("Patio missing required fields (name, prefix, count)")
                    return False
                
                total_tanks += patio['count']
            
            if total_tanks != 131:
                logger.warning(f"Total tank count is {total_tanks}, expected 131")
        
        # Check product distribution
        if 'product_distribution' in config:
            products = ['crudo', 'gasolina', 'diesel', 'fuel_jet', 'asfalto']
            for product in products:
                if product not in config['product_distribution']:
                    logger.error(f"Missing product {product} in product_distribution")
                    return False
        
        return True
    
    def validate_communication_config(self, config: Dict) -> bool:
        """
        Validate communication configuration.
        
        Args:
            config: Communication configuration dictionary
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required sections
        required_sections = ['mqtt', 'modbus', 'thingsboard_gateway']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required section in communication config: {section}")
                return False
        
        # Check MQTT configuration
        if 'mqtt' in config:
            required_mqtt_fields = ['broker', 'port', 'client_id']
            for field in required_mqtt_fields:
                if field not in config['mqtt']:
                    logger.error(f"Missing required field in mqtt config: {field}")
                    return False
        
        # Check Modbus configuration
        if 'modbus' in config:
            if 'server' not in config['modbus']:
                logger.error("Missing server section in modbus config")
                return False
            
            if 'registers' not in config['modbus']:
                logger.error("Missing registers section in modbus config")
                return False
        
        return True
