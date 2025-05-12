"""
Tank simulator module for simulating tank operations and fluid dynamics.
"""
import random
import time
from typing import Dict, List, Optional, Tuple

import yaml
import numpy as np

from ..models.tank import Tank, TankState, Product


class TankSimulator:
    """
    Class for simulating tank operations and fluid dynamics.
    
    Attributes:
        tanks (List[Tank]): List of tanks to simulate
        config (Dict): Simulation configuration
        last_update_time (float): Time of last simulation update
    """
    
    def __init__(self, tanks: List[Tank], config_path: str):
        """
        Initialize the tank simulator.
        
        Args:
            tanks: List of tanks to simulate
            config_path: Path to the simulation configuration file
        """
        self.tanks = tanks
        self.config = self._load_config(config_path)
        self.last_update_time = time.time()
        
        # Initialize random states for tanks
        self._initialize_tank_states()
    
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
    
    def _initialize_tank_states(self) -> None:
        """Initialize random states for tanks."""
        for tank in self.tanks:
            # Set a random initial level between 10% and 90% of capacity
            initial_fill_percentage = random.uniform(10, 90)
            initial_volume = (initial_fill_percentage / 100) * tank.capacity
            
            # Find the level corresponding to this volume using the strapping table
            # Find the closest volume in the strapping table
            levels = list(tank.strapping_table.keys())
            volumes = list(tank.strapping_table.values())
            
            # Find index of the closest volume
            closest_idx = min(range(len(volumes)), key=lambda i: abs(volumes[i] - initial_volume))
            initial_level = levels[closest_idx]
            
            # Update tank level
            tank.update_level(initial_level)
            
            # Set random initial state
            states = [TankState.FILLING, TankState.DRAINING, TankState.IDLE]
            weights = [0.2, 0.2, 0.6]  # Most tanks start idle
            initial_state = random.choices(states, weights=weights)[0]
            
            # If tank is in an operation state, set a random duration
            if initial_state != TankState.IDLE:
                # Get flow rate for this product
                product_key = tank.product.value
                flow_rates = self.config['operations']['flow_rates'][product_key]
                
                if initial_state == TankState.FILLING:
                    # Calculate how long it would take to fill the remaining capacity
                    remaining_capacity = tank.capacity - tank.current_volume
                    flow_rate = random.uniform(flow_rates['min_fill'], flow_rates['max_fill'])
                    max_duration = (remaining_capacity / flow_rate) * 3600  # Convert to seconds
                else:  # DRAINING
                    # Calculate how long it would take to drain the current volume
                    flow_rate = random.uniform(flow_rates['min_drain'], flow_rates['max_drain'])
                    max_duration = (tank.current_volume / flow_rate) * 3600  # Convert to seconds
                
                # Set a random duration, but not more than the max possible
                duration = random.uniform(1800, min(14400, max_duration))
                tank.set_state(initial_state, duration)
            else:
                tank.set_state(TankState.IDLE)
            
            # Set initial temperatures based on product type
            self._update_tank_temperatures(tank)
            
            # Set initial pressure
            self._update_tank_pressure(tank)
    
    def _update_tank_temperatures(self, tank: Tank) -> None:
        """
        Update temperatures for a tank based on product type and fill level.
        
        Args:
            tank: Tank to update
        """
        # Get temperature range for this product
        product_key = tank.product.value
        temp_range = self.config['operations']['temperature_ranges'][product_key]
        
        # Base temperature is a random value within the product's temperature range
        base_temp = random.uniform(temp_range['min'], temp_range['max'])
        
        # Temperature varies slightly at different heights in the tank
        # Higher points are typically cooler for hot products and warmer for cold products
        temp_gradient = (temp_range['max'] - temp_range['min']) * 0.2
        
        # Calculate fill height as a fraction of total height
        fill_fraction = tank.current_level / (tank.height * 1000)
        
        # Generate temperatures for each sensor
        # Assume sensors are evenly distributed from bottom to top
        temperatures = []
        for i in range(6):
            # Sensor position as fraction of height (0.0 to 1.0)
            sensor_position = (i + 0.5) / 6
            
            # If sensor is below liquid level, it measures liquid temperature
            if sensor_position <= fill_fraction:
                # Temperature varies with height
                if base_temp > 50:  # Hot product
                    # Hot products are cooler at the top
                    sensor_temp = base_temp - (sensor_position * temp_gradient)
                else:  # Cold product
                    # Cold products are warmer at the top
                    sensor_temp = base_temp + (sensor_position * temp_gradient)
                
                # Add small random variation
                sensor_temp += random.uniform(-1.0, 1.0)
            else:
                # Sensor is in vapor space, temperature is closer to ambient
                ambient_temp = self.config['environment']['ambient_temperature']
                sensor_temp = ambient_temp + random.uniform(-2.0, 2.0)
            
            temperatures.append(sensor_temp)
        
        # Update tank temperatures
        tank.update_temperatures(temperatures)
    
    def _update_tank_pressure(self, tank: Tank) -> None:
        """
        Update pressure for a tank based on product type and fill level.
        
        Args:
            tank: Tank to update
        """
        # Base pressure is atmospheric pressure (101.3 kPa)
        base_pressure = 101.3
        
        # Pressure varies based on product type and temperature
        if tank.product == Product.CRUDO or tank.product == Product.ASFALTO:
            # Hot products create more vapor pressure
            avg_temp = tank.get_average_temperature()
            # Simple model: pressure increases with temperature
            temp_factor = max(0, (avg_temp - 20) / 100)
            pressure_increase = temp_factor * 20  # Up to 20 kPa increase for hot products
            pressure = base_pressure + pressure_increase
        else:
            # Other products have less vapor pressure
            pressure = base_pressure + random.uniform(0, 5)
        
        # Update tank pressure
        tank.update_pressure(pressure)
    
    def _decide_next_tank_state(self, tank: Tank) -> Tuple[TankState, float]:
        """
        Decide the next state for a tank and its duration.
        
        Args:
            tank: Tank to update
            
        Returns:
            Tuple of (new state, duration in seconds)
        """
        # Get current fill percentage
        fill_percentage = tank.get_fill_percentage()
        
        # Probabilities depend on current fill level and state
        if tank.state == TankState.IDLE:
            # If tank is very empty, more likely to start filling
            if fill_percentage < 20:
                fill_prob = 0.7
                drain_prob = 0.1
                idle_prob = 0.2
            # If tank is very full, more likely to start draining
            elif fill_percentage > 80:
                fill_prob = 0.1
                drain_prob = 0.7
                idle_prob = 0.2
            # Otherwise, equal chances
            else:
                fill_prob = 0.3
                drain_prob = 0.3
                idle_prob = 0.4
        else:
            # If currently in an operation, more likely to go idle next
            idle_prob = 0.7
            
            # Other probabilities depend on current state
            if tank.state == TankState.FILLING:
                fill_prob = 0.1
                drain_prob = 0.2
            else:  # DRAINING
                fill_prob = 0.2
                drain_prob = 0.1
        
        # Select next state based on probabilities
        states = [TankState.FILLING, TankState.DRAINING, TankState.IDLE]
        weights = [fill_prob, drain_prob, idle_prob]
        next_state = random.choices(states, weights=weights)[0]
        
        # Determine duration based on state
        if next_state == TankState.IDLE:
            # Idle duration is between min and max rest time
            min_rest = self.config['operations']['min_rest_time']
            max_rest = self.config['operations']['max_rest_time']
            duration = random.uniform(min_rest, max_rest)
        else:
            # Get flow rate for this product
            product_key = tank.product.value
            flow_rates = self.config['operations']['flow_rates'][product_key]
            
            if next_state == TankState.FILLING:
                # Calculate how long it would take to fill the remaining capacity
                remaining_capacity = tank.capacity - tank.current_volume
                flow_rate = random.uniform(flow_rates['min_fill'], flow_rates['max_fill'])
                max_duration = (remaining_capacity / flow_rate) * 3600  # Convert to seconds
            else:  # DRAINING
                # Calculate how long it would take to drain the current volume
                flow_rate = random.uniform(flow_rates['min_drain'], flow_rates['max_drain'])
                max_duration = (tank.current_volume / flow_rate) * 3600  # Convert to seconds
            
            # Set a random duration, but not more than the max possible
            # and not less than 30 minutes or more than 4 hours
            duration = random.uniform(1800, min(14400, max_duration))
        
        return next_state, duration
    
    def update(self) -> None:
        """Update the simulation state for all tanks."""
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update each tank
        for tank in self.tanks:
            # Check if current operation has ended
            if tank.state != TankState.IDLE and current_time >= tank.operation_end_time:
                # Decide next state
                next_state, duration = self._decide_next_tank_state(tank)
                tank.set_state(next_state, duration)
            
            # Update tank level based on current state and elapsed time
            if tank.state == TankState.FILLING:
                # Calculate volume increase
                product_key = tank.product.value
                flow_rates = self.config['operations']['flow_rates'][product_key]
                flow_rate = random.uniform(flow_rates['min_fill'], flow_rates['max_fill'])
                
                # Convert barrels/hour to barrels/second
                flow_rate_per_second = flow_rate / 3600
                
                # Calculate volume increase
                volume_increase = flow_rate_per_second * elapsed_time
                
                # Update volume
                new_volume = min(tank.current_volume + volume_increase, tank.capacity)
                
                # Find the level corresponding to this volume
                # Find the closest volume in the strapping table
                levels = list(tank.strapping_table.keys())
                volumes = list(tank.strapping_table.values())
                
                # Find index of the closest volume
                closest_idx = min(range(len(volumes)), key=lambda i: abs(volumes[i] - new_volume))
                new_level = levels[closest_idx]
                
                # Update tank level
                tank.update_level(new_level)
                
            elif tank.state == TankState.DRAINING:
                # Calculate volume decrease
                product_key = tank.product.value
                flow_rates = self.config['operations']['flow_rates'][product_key]
                flow_rate = random.uniform(flow_rates['min_drain'], flow_rates['max_drain'])
                
                # Convert barrels/hour to barrels/second
                flow_rate_per_second = flow_rate / 3600
                
                # Calculate volume decrease
                volume_decrease = flow_rate_per_second * elapsed_time
                
                # Update volume
                new_volume = max(tank.current_volume - volume_decrease, 0)
                
                # Find the level corresponding to this volume
                # Find the closest volume in the strapping table
                levels = list(tank.strapping_table.keys())
                volumes = list(tank.strapping_table.values())
                
                # Find index of the closest volume
                closest_idx = min(range(len(volumes)), key=lambda i: abs(volumes[i] - new_volume))
                new_level = levels[closest_idx]
                
                # Update tank level
                tank.update_level(new_level)
            
            # Update temperatures and pressure
            self._update_tank_temperatures(tank)
            self._update_tank_pressure(tank)
