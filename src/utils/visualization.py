"""
Utility module for visualizing tank data.
"""
import os
import sys
import json
import time
import argparse
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.tank import Tank, TankState, Product


def create_tank_visualization(tanks: List[Tank], output_path: Optional[str] = None):
    """
    Create a visualization of tank levels and states.
    
    Args:
        tanks: List of tanks to visualize
        output_path: Path to save the visualization image (optional)
    """
    # Group tanks by patio
    patios = {}
    for tank in tanks:
        if tank.patio not in patios:
            patios[tank.patio] = []
        patios[tank.patio].append(tank)
    
    # Set up the figure and grid
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('Refinery Tank Simulator - Tank Status', fontsize=16)
    
    # Create a grid of subplots based on number of patios
    n_patios = len(patios)
    grid_size = (2, 2)  # 2x2 grid
    
    # Define colors for different products
    product_colors = {
        Product.CRUDO.value: 'black',
        Product.GASOLINA.value: 'orange',
        Product.DIESEL.value: 'brown',
        Product.FUEL_JET.value: 'blue',
        Product.ASFALTO.value: 'gray'
    }
    
    # Define colors for different states
    state_colors = {
        TankState.FILLING.value: 'green',
        TankState.DRAINING.value: 'red',
        TankState.IDLE.value: 'lightgray'
    }
    
    # Plot each patio
    for i, (patio_name, patio_tanks) in enumerate(patios.items()):
        # Create subplot
        ax = fig.add_subplot(grid_size[0], grid_size[1], i + 1)
        ax.set_title(f"{patio_name} ({len(patio_tanks)} tanks)")
        
        # Sort tanks by ID
        patio_tanks.sort(key=lambda t: t.id)
        
        # Calculate grid dimensions
        n_tanks = len(patio_tanks)
        grid_width = int(np.ceil(np.sqrt(n_tanks)))
        grid_height = int(np.ceil(n_tanks / grid_width))
        
        # Set up grid
        ax.set_xlim(0, grid_width)
        ax.set_ylim(0, grid_height)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Plot each tank
        for j, tank in enumerate(patio_tanks):
            # Calculate grid position
            x = j % grid_width
            y = grid_height - 1 - (j // grid_width)
            
            # Calculate fill level (0-1)
            fill_level = tank.get_fill_percentage() / 100.0
            
            # Create tank rectangle
            tank_width = 0.8
            tank_height = 0.8
            tank_rect = patches.Rectangle(
                (x + (1 - tank_width) / 2, y + (1 - tank_height) / 2),
                tank_width, tank_height,
                linewidth=1, edgecolor='black', facecolor='white'
            )
            
            # Create fill rectangle
            fill_rect = patches.Rectangle(
                (x + (1 - tank_width) / 2, y + (1 - tank_height) / 2),
                tank_width, tank_height * fill_level,
                linewidth=0, facecolor=product_colors[tank.product.value]
            )
            
            # Create state indicator
            state_indicator = patches.Circle(
                (x + 0.5, y + 0.9),
                0.05,
                facecolor=state_colors[tank.state.value]
            )
            
            # Add shapes to plot
            ax.add_patch(tank_rect)
            ax.add_patch(fill_rect)
            ax.add_patch(state_indicator)
            
            # Add tank ID
            ax.text(
                x + 0.5, y + 0.5,
                tank.id,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8
            )
            
            # Add fill percentage
            ax.text(
                x + 0.5, y + 0.2,
                f"{tank.get_fill_percentage():.1f}%",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=7,
                color='white' if fill_level > 0.3 else 'black'
            )
    
    # Add legend for products
    product_patches = [
        patches.Patch(color=color, label=product)
        for product, color in product_colors.items()
    ]
    fig.legend(
        handles=product_patches,
        loc='lower center',
        ncol=len(product_colors),
        bbox_to_anchor=(0.5, 0.02)
    )
    
    # Add legend for states
    state_patches = [
        patches.Patch(color=color, label=state)
        for state, color in state_colors.items()
    ]
    fig.legend(
        handles=state_patches,
        loc='lower center',
        ncol=len(state_colors),
        bbox_to_anchor=(0.5, 0.06)
    )
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.08, 1, 0.96])
    
    # Save or show the figure
    if output_path:
        plt.savefig(output_path, dpi=150)
        print(f"Visualization saved to {output_path}")
    else:
        plt.show()


def create_tank_level_chart(tank: Tank, history: List[Dict], output_path: Optional[str] = None):
    """
    Create a chart of tank level history.
    
    Args:
        tank: Tank to visualize
        history: List of historical tank states
        output_path: Path to save the chart image (optional)
    """
    # Extract data from history
    timestamps = [entry['timestamp'] for entry in history]
    levels = [entry['level'] for entry in history]
    volumes = [entry['volume'] for entry in history]
    states = [entry['state'] for entry in history]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f'Tank {tank.id} - Level and Volume History', fontsize=16)
    
    # Plot level
    ax1.plot(timestamps, levels, 'b-', linewidth=2)
    ax1.set_ylabel('Level (mm)')
    ax1.set_title('Tank Level')
    ax1.grid(True)
    
    # Add capacity line
    ax1.axhline(y=tank.height * 1000, color='r', linestyle='--', label='Tank Height')
    
    # Plot volume
    ax2.plot(timestamps, volumes, 'g-', linewidth=2)
    ax2.set_ylabel('Volume (barrels)')
    ax2.set_xlabel('Time')
    ax2.set_title('Tank Volume')
    ax2.grid(True)
    
    # Add capacity line
    ax2.axhline(y=tank.capacity, color='r', linestyle='--', label='Tank Capacity')
    
    # Add state indicators
    for i in range(1, len(timestamps)):
        if states[i] != states[i-1]:
            ax1.axvline(x=timestamps[i], color='gray', linestyle=':')
            ax2.axvline(x=timestamps[i], color='gray', linestyle=':')
            ax2.text(
                timestamps[i], min(volumes),
                states[i],
                rotation=90,
                verticalalignment='bottom',
                fontsize=8
            )
    
    # Add legends
    ax1.legend()
    ax2.legend()
    
    # Adjust layout
    plt.tight_layout()
    
    # Save or show the figure
    if output_path:
        plt.savefig(output_path, dpi=150)
        print(f"Chart saved to {output_path}")
    else:
        plt.show()


def main():
    """Main entry point for visualization utility."""
    parser = argparse.ArgumentParser(description='Tank Visualization Utility')
    parser.add_argument('--data-file', type=str, required=True,
                        help='Path to tank data JSON file')
    parser.add_argument('--output', type=str, default=None,
                        help='Path to save visualization image')
    parser.add_argument('--type', type=str, choices=['overview', 'chart'], default='overview',
                        help='Type of visualization to create')
    parser.add_argument('--tank-id', type=str, default=None,
                        help='Tank ID for chart visualization')
    args = parser.parse_args()
    
    # Load tank data
    with open(args.data_file, 'r') as file:
        data = json.load(file)
    
    if args.type == 'overview':
        # Create tanks from data
        tanks = [Tank.from_dict(tank_data) for tank_data in data['tanks']]
        create_tank_visualization(tanks, args.output)
    
    elif args.type == 'chart':
        if not args.tank_id:
            print("Error: Tank ID is required for chart visualization")
            sys.exit(1)
        
        # Find tank with matching ID
        tank_data = next((t for t in data['tanks'] if t['id'] == args.tank_id), None)
        if not tank_data:
            print(f"Error: Tank with ID {args.tank_id} not found")
            sys.exit(1)
        
        # Create tank from data
        tank = Tank.from_dict(tank_data)
        
        # Get history for this tank
        if 'history' not in data or args.tank_id not in data['history']:
            print(f"Error: No history found for tank {args.tank_id}")
            sys.exit(1)
        
        history = data['history'][args.tank_id]
        create_tank_level_chart(tank, history, args.output)


if __name__ == '__main__':
    main()
