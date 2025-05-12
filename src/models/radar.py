"""
Radar model for the refinery tank simulator.
This module defines the Radar class which simulates a SAAB radar sensor.
"""
import random
from typing import Dict, List, Optional, Tuple

from .tank import Tank


class Radar:
    """
    Class representing a SAAB radar sensor installed on a tank.
    
    Attributes:
        tank_id (str): ID of the tank this radar is installed on
        modbus_address (int): Modbus RTU address of this radar
        installation_height (float): Height of radar installation from tank bottom in mm
        fine_adjustment (float): Fine adjustment offset in mm
        measurement_error (float): Simulated measurement error in mm
        level_reading (float): Current level reading in mm
        temperature_readings (List[float]): Current temperature readings
        pressure_reading (float): Current pressure reading
    """
    
    def __init__(
        self,
        tank_id: str,
        modbus_address: int,
        installation_height: float,
        measurement_error: float = 1.0,
        fine_adjustment: float = 0.0
    ):
        """
        Initialize a new Radar instance.
        
        Args:
            tank_id: ID of the tank this radar is installed on
            modbus_address: Modbus RTU address of this radar
            installation_height: Height of radar installation from tank bottom in mm
            measurement_error: Simulated measurement error in mm
            fine_adjustment: Fine adjustment offset in mm
        """
        self.tank_id = tank_id
        self.modbus_address = modbus_address
        self.installation_height = installation_height
        self.measurement_error = measurement_error
        self.fine_adjustment = fine_adjustment
        
        # Current readings
        self.level_reading = 0.0
        self.temperature_readings = [0.0] * 6
        self.pressure_reading = 0.0
    
    def measure_level(self, tank: Tank) -> float:
        """
        Measure the level of product in the tank.
        
        Args:
            tank: Tank to measure
            
        Returns:
            Measured level in mm
        """
        # Get actual level from tank
        actual_level = tank.current_level
        
        # Calculate distance from radar to liquid surface
        # (installation_height - actual_level) is the distance from radar to liquid
        distance_to_liquid = self.installation_height - actual_level
        
        # Apply fine adjustment
        adjusted_distance = distance_to_liquid + self.fine_adjustment
        
        # Apply measurement error (random noise)
        error = random.uniform(-self.measurement_error, self.measurement_error)
        measured_distance = adjusted_distance + error
        
        # Convert back to level from bottom
        measured_level = self.installation_height - measured_distance
        
        # Ensure level is not negative
        measured_level = max(0, measured_level)
        
        # Update current reading
        self.level_reading = measured_level
        
        return measured_level
    
    def measure_temperatures(self, tank: Tank) -> List[float]:
        """
        Measure temperatures at different points in the tank.
        
        Args:
            tank: Tank to measure
            
        Returns:
            List of temperature readings
        """
        # Get actual temperatures from tank
        actual_temperatures = tank.temperatures
        
        # Apply measurement errors
        measured_temperatures = []
        for temp in actual_temperatures:
            # Add small random error to each temperature reading
            error = random.uniform(-0.5, 0.5)
            measured_temp = temp + error
            measured_temperatures.append(measured_temp)
        
        # Update current readings
        self.temperature_readings = measured_temperatures
        
        return measured_temperatures
    
    def measure_pressure(self, tank: Tank) -> float:
        """
        Measure pressure in the tank.
        
        Args:
            tank: Tank to measure
            
        Returns:
            Measured pressure in kPa
        """
        # Get actual pressure from tank
        actual_pressure = tank.pressure
        
        # Apply measurement error
        error = random.uniform(-0.1, 0.1) * actual_pressure
        measured_pressure = actual_pressure + error
        
        # Update current reading
        self.pressure_reading = measured_pressure
        
        return measured_pressure
    
    def update_installation_height(self, new_height: float) -> None:
        """
        Update the installation height of the radar.
        
        Args:
            new_height: New installation height in mm
        """
        self.installation_height = new_height
    
    def update_fine_adjustment(self, new_adjustment: float) -> None:
        """
        Update the fine adjustment offset of the radar.
        
        Args:
            new_adjustment: New fine adjustment offset in mm
        """
        self.fine_adjustment = new_adjustment
    
    def to_dict(self) -> Dict:
        """
        Convert the radar to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the radar
        """
        return {
            "tank_id": self.tank_id,
            "modbus_address": self.modbus_address,
            "installation_height": self.installation_height,
            "measurement_error": self.measurement_error,
            "fine_adjustment": self.fine_adjustment,
            "level_reading": self.level_reading,
            "temperature_readings": self.temperature_readings,
            "pressure_reading": self.pressure_reading
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Radar':
        """
        Create a radar from a dictionary.
        
        Args:
            data: Dictionary representation of a radar
            
        Returns:
            Radar instance
        """
        radar = cls(
            tank_id=data["tank_id"],
            modbus_address=data["modbus_address"],
            installation_height=data["installation_height"],
            measurement_error=data.get("measurement_error", 1.0),
            fine_adjustment=data.get("fine_adjustment", 0.0)
        )
        
        # Set current readings
        radar.level_reading = data.get("level_reading", 0.0)
        radar.temperature_readings = data.get("temperature_readings", [0.0] * 6)
        radar.pressure_reading = data.get("pressure_reading", 0.0)
        
        return radar
