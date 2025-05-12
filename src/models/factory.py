"""
Factory module for creating tanks and radars based on configuration.
"""
import random
from typing import Dict, List, Tuple

import yaml

from .tank import Tank, TankType, Product
from .radar import Radar


class TankFactory:
    """
    Factory class for creating tanks and radars based on configuration.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the factory with configuration.
        
        Args:
            config_path: Path to the tank configuration file
        """
        self.config = self._load_config(config_path)
    
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
    
    def create_tanks_and_radars(self) -> Tuple[List[Tank], List[Radar]]:
        """
        Create tanks and radars based on configuration.
        
        Returns:
            Tuple containing lists of tanks and radars
        """
        tanks = []
        radars = []
        modbus_address = 1  # Start with address 1
        
        # Get product distribution
        product_distribution = self.config['product_distribution']
        products = list(product_distribution.keys())
        product_weights = list(product_distribution.values())
        
        # Get tank types
        tank_types = self.config['tank_types']
        tank_type_names = list(tank_types.keys())
        tank_type_weights = [tank_types[t]['probability'] for t in tank_type_names]
        
        # Create tanks for each patio
        for patio_config in self.config['patios']:
            patio_name = patio_config['name']
            prefix = patio_config['prefix']
            count = patio_config['count']
            
            # Get tank size distribution for this patio
            size_distribution = patio_config['tank_sizes']
            
            # Calculate how many tanks of each size to create
            small_count = int(count * size_distribution['small'])
            medium_count = int(count * size_distribution['medium'])
            large_count = count - small_count - medium_count  # Ensure we get exactly 'count' tanks
            
            # Create tanks for this patio
            for i in range(1, count + 1):
                # Determine tank size
                if i <= small_count:
                    size_category = 'small'
                elif i <= small_count + medium_count:
                    size_category = 'medium'
                else:
                    size_category = 'large'
                
                # Get size range for this category
                size_range = self.config['tank_size_ranges'][size_category]
                
                # Generate random capacity within range
                capacity = random.uniform(
                    size_range['min_capacity'],
                    size_range['max_capacity']
                )
                
                # Generate random height within range
                height = random.uniform(
                    size_range['min_height'],
                    size_range['max_height']
                )
                
                # Calculate diameter based on capacity and height
                # V = π × r² × h, where V is volume in cubic meters
                # 1 barrel = 0.159 cubic meters
                volume_m3 = capacity * 0.159
                radius_m = ((volume_m3 / (math.pi * height)) ** 0.5)
                diameter = radius_m * 2
                
                # Generate tank ID
                tank_id = f"{prefix}-TK-{i:02d}"
                
                # Select random product
                product_name = random.choices(products, weights=product_weights)[0]
                product = Product(product_name)
                
                # Select random tank type
                tank_type_name = random.choices(tank_type_names, weights=tank_type_weights)[0]
                tank_type = TankType(tank_type_name)
                
                # Get deformation factor and additional parameters for this tank type
                deformation_factor = tank_types[tank_type_name]['deformation_factor']
                additional_params = {k: v for k, v in tank_types[tank_type_name].items() 
                                    if k not in ['probability', 'description', 'deformation_factor']}
                
                # Create tank
                tank = Tank(
                    tank_id=tank_id,
                    patio=patio_name,
                    product=product,
                    height=height,
                    diameter=diameter,
                    capacity=capacity,
                    tank_type=tank_type,
                    deformation_factor=deformation_factor,
                    additional_params=additional_params
                )
                
                # Create radar for this tank
                # Installation height is tank height in mm plus some margin
                installation_height = height * 1000 + 200  # 200mm margin
                
                radar = Radar(
                    tank_id=tank_id,
                    modbus_address=modbus_address,
                    installation_height=installation_height,
                    measurement_error=random.uniform(0.5, 2.0),  # Random error between 0.5 and 2.0 mm
                    fine_adjustment=random.uniform(-5.0, 5.0)  # Random fine adjustment between -5 and 5 mm
                )
                
                # Add tank and radar to lists
                tanks.append(tank)
                radars.append(radar)
                
                # Increment Modbus address
                modbus_address += 1
        
        return tanks, radars


# Import math here to avoid circular import
import math
