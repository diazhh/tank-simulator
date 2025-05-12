"""
Tank model for the refinery tank simulator.
This module defines the Tank class which represents a physical tank in the refinery.
"""
import math
import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class TankState(Enum):
    """Enum representing the possible states of a tank."""
    FILLING = "filling"
    DRAINING = "draining"
    IDLE = "idle"


class TankType(Enum):
    """Enum representing the possible types of tanks."""
    STANDARD = "standard"
    FLOATING_ROOF = "floating_roof"
    CONICAL_BOTTOM = "conical_bottom"


class Product(Enum):
    """Enum representing the possible products stored in a tank."""
    CRUDO = "crudo"
    GASOLINA = "gasolina"
    DIESEL = "diesel"
    FUEL_JET = "fuel_jet"
    ASFALTO = "asfalto"


class Tank:
    """
    Class representing a physical tank in the refinery.
    
    Attributes:
        id (str): Unique identifier for the tank
        patio (str): Name of the patio where the tank is located
        product (Product): Type of product stored in the tank
        height (float): Height of the tank in meters
        diameter (float): Diameter of the tank in meters
        capacity (float): Capacity of the tank in barrels
        tank_type (TankType): Type of tank
        state (TankState): Current state of the tank
        current_level (float): Current level of product in the tank in millimeters
        current_volume (float): Current volume of product in the tank in barrels
        strapping_table (Dict[int, float]): Table relating level to volume
        temperatures (List[float]): List of temperature readings at different points
        pressure (float): Pressure reading in the tank
        operation_end_time (float): Time when the current operation will end
    """
    
    def __init__(
        self,
        tank_id: str,
        patio: str,
        product: Product,
        height: float,
        diameter: float,
        capacity: float,
        tank_type: TankType = TankType.STANDARD,
        deformation_factor: float = 0.0,
        additional_params: Optional[Dict] = None
    ):
        """
        Initialize a new Tank instance.
        
        Args:
            tank_id: Unique identifier for the tank
            patio: Name of the patio where the tank is located
            product: Type of product stored in the tank
            height: Height of the tank in meters
            diameter: Diameter of the tank in meters
            capacity: Capacity of the tank in barrels
            tank_type: Type of tank (default: STANDARD)
            deformation_factor: Factor representing tank deformation (0.0 to 1.0)
            additional_params: Additional parameters specific to the tank type
        """
        self.id = tank_id
        self.patio = patio
        self.product = product
        self.height = height
        self.diameter = diameter
        self.capacity = capacity
        self.tank_type = tank_type
        self.deformation_factor = deformation_factor
        self.additional_params = additional_params or {}
        
        # Dynamic state
        self.state = TankState.IDLE
        self.current_level = 0.0  # mm from bottom
        self.current_volume = 0.0  # barrels
        self.temperatures = [20.0] * 6  # 6 temperature sensors
        self.pressure = 101.3  # kPa (atmospheric pressure)
        self.operation_end_time = 0.0
        
        # Generate strapping table
        self.strapping_table = self._generate_strapping_table()
    
    def _generate_strapping_table(self) -> Dict[int, float]:
        """
        Generate a strapping table for the tank with 100mm resolution.
        
        Returns:
            Dict mapping level (mm) to volume (barrels)
        """
        # Convert height from meters to millimeters
        height_mm = self.height * 1000
        
        # Create a table with 100mm resolution
        table = {}
        
        # Conversion factor: 1 cubic meter = 6.29 barrels
        m3_to_barrels = 6.29
        
        # Calculate tank radius in meters
        radius = self.diameter / 2
        
        # Calculate tank area in square meters
        area = math.pi * (radius ** 2)
        
        # For each 100mm increment of height (0, 100, 200, ..., height_mm)
        for level in range(0, int(height_mm) + 1, 100):
            # Convert level from mm to meters
            level_m = level / 1000
            
            # Calculate volume based on tank type
            if self.tank_type == TankType.STANDARD:
                # Standard cylindrical tank
                volume_m3 = area * level_m
                
                # Apply deformation if any
                if self.deformation_factor > 0:
                    # Simple deformation model: volume decreases slightly at higher levels
                    deformation = 1.0 - (self.deformation_factor * (level_m / self.height) ** 2)
                    volume_m3 *= deformation
                
            elif self.tank_type == TankType.FLOATING_ROOF:
                # Tank with floating roof
                # The roof displaces some volume when it's floating
                if level_m < 0.3 * self.height:  # Roof resting on supports
                    volume_m3 = area * level_m
                else:
                    # Account for roof displacement
                    roof_weight = self.additional_params.get('roof_weight', 15000)  # kg
                    # Crude oil density ~900 kg/m³
                    roof_displacement = roof_weight / 900
                    volume_m3 = area * level_m - roof_displacement
                
            elif self.tank_type == TankType.CONICAL_BOTTOM:
                # Tank with conical bottom
                cone_angle = self.additional_params.get('cone_angle', 15)  # degrees
                cone_height = radius * math.tan(math.radians(cone_angle))
                
                if level_m <= cone_height:
                    # Within the cone section
                    cone_radius_at_level = (level_m / cone_height) * radius
                    volume_m3 = (1/3) * math.pi * level_m * (cone_radius_at_level ** 2)
                else:
                    # Above the cone section
                    cone_volume = (1/3) * math.pi * cone_height * (radius ** 2)
                    cylinder_volume = area * (level_m - cone_height)
                    volume_m3 = cone_volume + cylinder_volume
            else:
                # Default to standard cylindrical calculation
                volume_m3 = area * level_m
            
            # Convert to barrels and store in table
            table[level] = round(volume_m3 * m3_to_barrels, 2)  # Redondear a 2 decimales
        
        # Asegurar que el nivel máximo esté incluido si no es múltiplo de 100
        max_level = int(height_mm)
        if max_level % 100 != 0 and max_level not in table:
            level_m = max_level / 1000
            # Calcular volumen para el nivel máximo
            if self.tank_type == TankType.STANDARD:
                volume_m3 = area * level_m
                if self.deformation_factor > 0:
                    deformation = 1.0 - (self.deformation_factor * (level_m / self.height) ** 2)
                    volume_m3 *= deformation
            elif self.tank_type == TankType.FLOATING_ROOF:
                if level_m < 0.3 * self.height:
                    volume_m3 = area * level_m
                else:
                    roof_weight = self.additional_params.get('roof_weight', 15000)
                    roof_displacement = roof_weight / 900
                    volume_m3 = area * level_m - roof_displacement
            elif self.tank_type == TankType.CONICAL_BOTTOM:
                cone_angle = self.additional_params.get('cone_angle', 15)
                cone_height = radius * math.tan(math.radians(cone_angle))
                if level_m <= cone_height:
                    cone_radius_at_level = (level_m / cone_height) * radius
                    volume_m3 = (1/3) * math.pi * level_m * (cone_radius_at_level ** 2)
                else:
                    cone_volume = (1/3) * math.pi * cone_height * (radius ** 2)
                    cylinder_volume = area * (level_m - cone_height)
                    volume_m3 = cone_volume + cylinder_volume
            else:
                volume_m3 = area * level_m
            
            table[max_level] = round(volume_m3 * m3_to_barrels, 2)
        
        return table
    
    def update_level(self, new_level: float) -> None:
        """
        Update the current level of the tank.
        
        Args:
            new_level: New level in millimeters
        """
        # Ensure level is within tank bounds
        new_level = max(0, min(new_level, self.height * 1000))
        self.current_level = new_level
        
        # Update volume based on strapping table
        level_int = int(new_level)
        if level_int in self.strapping_table:
            self.current_volume = self.strapping_table[level_int]
        else:
            # Interpolate if exact level not in table
            lower_level = max(k for k in self.strapping_table.keys() if k <= level_int)
            upper_level = min(k for k in self.strapping_table.keys() if k >= level_int)
            
            lower_volume = self.strapping_table[lower_level]
            upper_volume = self.strapping_table[upper_level]
            
            # Linear interpolation
            self.current_volume = lower_volume + (upper_volume - lower_volume) * \
                                 (new_level - lower_level) / (upper_level - lower_level)
    
    def update_temperatures(self, temperatures: List[float]) -> None:
        """
        Update the temperature readings for the tank.
        
        Args:
            temperatures: List of temperature readings
        """
        if len(temperatures) != len(self.temperatures):
            raise ValueError(f"Expected {len(self.temperatures)} temperature readings, got {len(temperatures)}")
        
        self.temperatures = temperatures.copy()
    
    def update_pressure(self, pressure: float) -> None:
        """
        Update the pressure reading for the tank.
        
        Args:
            pressure: New pressure reading in kPa
        """
        self.pressure = pressure
    
    def set_state(self, state: TankState, duration: float = 0.0) -> None:
        """
        Set the state of the tank and the duration of the operation.
        
        Args:
            state: New state
            duration: Duration of the operation in seconds
        """
        self.state = state
        if duration > 0:
            self.operation_end_time = time.time() + duration
    
    def get_fill_percentage(self) -> float:
        """
        Get the fill percentage of the tank.
        
        Returns:
            Fill percentage (0.0 to 100.0)
        """
        return (self.current_volume / self.capacity) * 100.0
    
    def get_average_temperature(self) -> float:
        """
        Get the average temperature from all sensors.
        
        Returns:
            Average temperature in degrees Celsius
        """
        return sum(self.temperatures) / len(self.temperatures)
    
    def to_dict(self) -> Dict:
        """
        Convert the tank to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the tank
        """
        return {
            "id": self.id,
            "patio": self.patio,
            "product": self.product.value,
            "height": self.height,
            "diameter": self.diameter,
            "capacity": self.capacity,
            "tank_type": self.tank_type.value,
            "deformation_factor": self.deformation_factor,
            "additional_params": self.additional_params,
            "state": self.state.value,
            "current_level": self.current_level,
            "current_volume": self.current_volume,
            "fill_percentage": self.get_fill_percentage(),
            "temperatures": self.temperatures,
            "average_temperature": self.get_average_temperature(),
            "pressure": self.pressure
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tank':
        """
        Create a tank from a dictionary.
        
        Args:
            data: Dictionary representation of a tank
            
        Returns:
            Tank instance
        """
        tank = cls(
            tank_id=data["id"],
            patio=data["patio"],
            product=Product(data["product"]),
            height=data["height"],
            diameter=data["diameter"],
            capacity=data["capacity"],
            tank_type=TankType(data["tank_type"]),
            deformation_factor=data["deformation_factor"],
            additional_params=data["additional_params"]
        )
        
        # Set dynamic state
        tank.state = TankState(data["state"])
        tank.update_level(data["current_level"])
        tank.update_temperatures(data["temperatures"])
        tank.update_pressure(data["pressure"])
        
        return tank
