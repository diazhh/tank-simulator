"""
Utility module for generating sample tank data for testing and visualization.
"""
import os
import sys
import json
import random
import argparse
import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.factory import TankFactory
from src.models.tank import Tank, TankState, Product


def generate_sample_data(config_path: str, output_path: str, include_history: bool = False, history_days: int = 7):
    """
    Generate sample tank data for testing and visualization.
    
    Args:
        config_path: Path to the tanks configuration file
        output_path: Path to save the generated data
        include_history: Whether to include historical data
        history_days: Number of days of historical data to generate
    """
    # Create tanks using factory
    tank_factory = TankFactory(config_path)
    tanks, radars = tank_factory.create_tanks_and_radars()
    
    # Create data dictionary
    data = {
        'tanks': [tank.to_dict() for tank in tanks],
        'radars': [radar.to_dict() for radar in radars]
    }
    
    # Generate historical data if requested
    if include_history:
        print(f"Generating {history_days} days of historical data...")
        data['history'] = generate_historical_data(tanks, history_days)
    
    # Save data to file
    with open(output_path, 'w') as file:
        json.dump(data, file, indent=2)
    
    print(f"Generated data for {len(tanks)} tanks and {len(radars)} radars")
    print(f"Data saved to {output_path}")


def generate_historical_data(tanks: List[Tank], days: int) -> Dict[str, List[Dict]]:
    """
    Generate historical data for tanks.
    
    Args:
        tanks: List of tanks to generate history for
        days: Number of days of history to generate
        
    Returns:
        Dictionary mapping tank IDs to lists of historical states
    """
    history = {}
    
    # Current time
    now = datetime.datetime.now()
    
    # Generate history for each tank
    for tank in tanks:
        tank_history = []
        
        # Start with current state
        current_level = tank.current_level
        current_volume = tank.current_volume
        current_state = tank.state
        
        # Generate data points at 1-hour intervals
        for hour in range(days * 24, 0, -1):
            # Calculate timestamp
            timestamp = (now - datetime.timedelta(hours=hour)).isoformat()
            
            # Decide if state should change
            if random.random() < 0.1:  # 10% chance of state change each hour
                # Choose a new state
                new_state = random.choice(list(TankState))
                
                # Don't allow same state
                while new_state == current_state:
                    new_state = random.choice(list(TankState))
                
                current_state = new_state
            
            # Update level and volume based on state
            if current_state == TankState.FILLING:
                # Increase level
                level_change = random.uniform(50, 200)  # 50-200 mm per hour
                new_level = min(current_level + level_change, tank.height * 1000)
                
                # Calculate corresponding volume
                level_int = int(new_level)
                if level_int in tank.strapping_table:
                    new_volume = tank.strapping_table[level_int]
                else:
                    # Interpolate
                    lower_level = max(k for k in tank.strapping_table.keys() if k <= level_int)
                    upper_level = min(k for k in tank.strapping_table.keys() if k >= level_int)
                    
                    lower_volume = tank.strapping_table[lower_level]
                    upper_volume = tank.strapping_table[upper_level]
                    
                    # Linear interpolation
                    new_volume = lower_volume + (upper_volume - lower_volume) * \
                                (new_level - lower_level) / (upper_level - lower_level)
            
            elif current_state == TankState.DRAINING:
                # Decrease level
                level_change = random.uniform(50, 200)  # 50-200 mm per hour
                new_level = max(current_level - level_change, 0)
                
                # Calculate corresponding volume
                level_int = int(new_level)
                if level_int in tank.strapping_table:
                    new_volume = tank.strapping_table[level_int]
                else:
                    # Interpolate
                    if new_level <= 0:
                        new_volume = 0
                    else:
                        lower_level = max(k for k in tank.strapping_table.keys() if k <= level_int)
                        upper_level = min(k for k in tank.strapping_table.keys() if k >= level_int)
                        
                        lower_volume = tank.strapping_table[lower_level]
                        upper_volume = tank.strapping_table[upper_level]
                        
                        # Linear interpolation
                        new_volume = lower_volume + (upper_volume - lower_volume) * \
                                    (new_level - lower_level) / (upper_level - lower_level)
            
            else:  # IDLE
                # Small random fluctuation
                level_change = random.uniform(-5, 5)  # -5 to 5 mm per hour
                new_level = max(0, min(current_level + level_change, tank.height * 1000))
                
                # Calculate corresponding volume
                level_int = int(new_level)
                if level_int in tank.strapping_table:
                    new_volume = tank.strapping_table[level_int]
                else:
                    # Interpolate
                    lower_level = max(k for k in tank.strapping_table.keys() if k <= level_int)
                    upper_level = min(k for k in tank.strapping_table.keys() if k >= level_int)
                    
                    lower_volume = tank.strapping_table[lower_level]
                    upper_volume = tank.strapping_table[upper_level]
                    
                    # Linear interpolation
                    new_volume = lower_volume + (upper_volume - lower_volume) * \
                                (new_level - lower_level) / (upper_level - lower_level)
            
            # Update current values
            current_level = new_level
            current_volume = new_volume
            
            # Add data point to history
            tank_history.append({
                'timestamp': timestamp,
                'level': current_level,
                'volume': current_volume,
                'state': current_state.value,
                'fill_percentage': (current_volume / tank.capacity) * 100.0
            })
        
        # Add tank history to overall history
        history[tank.id] = tank_history
    
    return history


def main():
    """Main entry point for data generator utility."""
    parser = argparse.ArgumentParser(description='Tank Data Generator Utility')
    parser.add_argument('--config', type=str, default='../config/tanks.yaml',
                        help='Path to tanks configuration file')
    parser.add_argument('--output', type=str, default='../data/sample_data.json',
                        help='Path to save generated data')
    parser.add_argument('--history', action='store_true',
                        help='Include historical data')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days of historical data to generate')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Generate sample data
    generate_sample_data(args.config, args.output, args.history, args.days)


if __name__ == '__main__':
    main()
