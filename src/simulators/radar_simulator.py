"""
Radar simulator module for simulating radar measurements.
"""
import random
import time
from typing import Dict, List, Optional, Tuple

import yaml

from ..models.tank import Tank
from ..models.radar import Radar


class RadarSimulator:
    """
    Class for simulating radar measurements.
    
    Attributes:
        radars (List[Radar]): List of radars to simulate
        tanks (Dict[str, Tank]): Dictionary mapping tank IDs to tanks
        config (Dict): Simulation configuration
        last_update_time (float): Time of last simulation update
    """
    
    def __init__(self, radars: List[Radar], tanks: List[Tank], config_path: str):
        """
        Initialize the radar simulator.
        
        Args:
            radars: List of radars to simulate
            tanks: List of tanks being monitored
            config_path: Path to the simulation configuration file
        """
        self.radars = radars
        # Create a dictionary for quick lookup of tanks by ID
        self.tanks = {tank.id: tank for tank in tanks}
        self.config = self._load_config(config_path)
        self.last_update_time = time.time()
    
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
    
    def update(self) -> None:
        """Update the radar measurements for all radars."""
        current_time = time.time()
        self.last_update_time = current_time
        
        # Get radar configuration
        radar_config = self.config.get('radar', {})
        measurement_error = radar_config.get('measurement_error', 1.0)
        
        # Update each radar
        for radar in self.radars:
            # Get the tank this radar is monitoring
            tank_id = radar.tank_id
            if tank_id not in self.tanks:
                continue
            
            tank = self.tanks[tank_id]
            
            # Update radar's measurement error based on config and some randomness
            radar.measurement_error = measurement_error * random.uniform(0.8, 1.2)
            
            # Measure level
            radar.measure_level(tank)
            
            # Measure temperatures
            radar.measure_temperatures(tank)
            
            # Measure pressure
            radar.measure_pressure(tank)
    
    def get_modbus_registers(self) -> Dict[int, Dict]:
        """
        Get the current Modbus register values for all radars.
        
        Returns:
            Dictionary mapping Modbus addresses to register dictionaries
        """
        registers = {}
        
        for radar in self.radars:
            # Create register dictionary for this radar
            radar_registers = {
                'level': int(radar.level_reading),
                'temperature_1': int(radar.temperature_readings[0] * 10),  # Scale by 10 for precision
                'temperature_2': int(radar.temperature_readings[1] * 10),
                'temperature_3': int(radar.temperature_readings[2] * 10),
                'temperature_4': int(radar.temperature_readings[3] * 10),
                'temperature_5': int(radar.temperature_readings[4] * 10),
                'temperature_6': int(radar.temperature_readings[5] * 10),
                'pressure': int(radar.pressure_reading * 100),  # Scale by 100 for precision
                'radar_height': int(radar.installation_height),
                'fine_adjustment': int(radar.fine_adjustment * 10)  # Scale by 10 for precision
            }
            
            registers[radar.modbus_address] = radar_registers
        
        return registers
    
    def update_radar_configuration(self, modbus_address: int, register_name: str, value: int) -> bool:
        """
        Update radar configuration based on Modbus register write.
        
        Args:
            modbus_address: Modbus address of the radar
            register_name: Name of the register being written
            value: New value for the register
            
        Returns:
            True if update was successful, False otherwise
        """
        # Find the radar with this Modbus address
        radar = next((r for r in self.radars if r.modbus_address == modbus_address), None)
        if not radar:
            return False
        
        # Update radar configuration based on register name
        if register_name == 'radar_height':
            radar.update_installation_height(value)
            return True
        elif register_name == 'fine_adjustment':
            # Convert from scaled integer to float
            fine_adjustment = value / 10.0
            radar.update_fine_adjustment(fine_adjustment)
            return True
        
        # Unknown register
        return False
