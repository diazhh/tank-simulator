# Refinery Tank Simulator User Manual

## Introduction

The Refinery Tank Simulator is a comprehensive tool designed to simulate the behavior of 131 refinery tanks across 4 patios, their SAAB radar sensors, and integration with ThingsBoard via MQTT and Modbus RTU protocols.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Network connectivity to ThingsBoard server (if using integration)

### Setup

1. Clone or download the simulator repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Review and modify configuration files in the `config/` directory

## Configuration

The simulator uses YAML configuration files located in the `config/` directory:

### simulation.yaml

Controls the simulation parameters:
- Update intervals
- Environmental factors
- Flow rates for different products
- Temperature ranges
- Radar simulation parameters

### tanks.yaml

Defines the tank properties:
- Patio definitions and tank counts
- Tank size distributions
- Product distributions
- Tank types and characteristics

### communication.yaml

Configures communication protocols:
- MQTT broker settings for ThingsBoard
- Modbus server configuration
- Register mappings
- ThingsBoard Gateway settings

## Running the Simulator

To start the simulator with default configuration:

```bash
python src/main.py
```

To specify a custom configuration directory:

```bash
python src/main.py --config-dir /path/to/config
```

## Simulator Components

### Tank Models

The simulator creates 131 tanks distributed across 4 patios:
- Cerro de Carga: 20 tanks
- Osanco: 28 tanks
- Chaure: 23 tanks
- Refinería: 60 tanks

Each tank has:
- Unique identifier (e.g., CRG-TK-01)
- Product type (crudo, gasolina, diesel, fuel jet, asfalto)
- Physical dimensions (height, diameter)
- Capacity in barrels
- Strapping table (level-to-volume conversion)
- Dynamic state (filling, draining, idle)

### Radar Sensors

Each tank has a SAAB radar sensor that measures:
- Level (distance from tank bottom to liquid surface)
- Temperature (6 points throughout the tank)
- Pressure

Radar configuration parameters:
- Installation height (distance from tank bottom to radar)
- Fine adjustment offset (calibration parameter)

### Communication Interfaces

#### MQTT Client

Sends tank data to ThingsBoard:
- Static attributes (dimensions, product type, etc.)
- Dynamic telemetry (level, volume, temperature, etc.)

#### Modbus RTU Server

Exposes radar data via Modbus protocol:
- Level measurements
- Temperature readings
- Pressure readings
- Configuration parameters

## Monitoring the Simulator

The simulator logs information to both the console and log files in the `logs/` directory. The log level can be configured in `simulation.yaml`.

Example log output:
```
2025-05-12 14:30:45.123 | INFO | src.main:run:245 - Running with update interval of 60 seconds
2025-05-12 14:31:45.456 | DEBUG | src.main:run:262 - Update completed in 0.35 seconds, sleeping for 59.65 seconds
```

## ThingsBoard Integration

See `docs/thingsboard_integration.md` for detailed instructions on integrating with ThingsBoard.

## Troubleshooting

### Common Issues

1. **MQTT Connection Failure**
   - Check broker address and port
   - Verify credentials
   - Ensure network connectivity

2. **Modbus Server Errors**
   - Check if port is already in use
   - Verify server address configuration
   - Check firewall settings

3. **Configuration Errors**
   - Validate YAML syntax
   - Check for missing required fields
   - Ensure consistent units (meters, millimeters, etc.)

### Getting Help

If you encounter issues:
1. Check the log files in the `logs/` directory
2. Review configuration files for errors
3. Consult the documentation in the `docs/` directory

## Advanced Usage

### Custom Tank Configurations

You can modify the `tanks.yaml` file to create custom tank configurations:
- Change the distribution of tank sizes
- Adjust product probabilities
- Define new tank types with specific characteristics

### Simulation Scenarios

Create different simulation scenarios by modifying `simulation.yaml`:
- Adjust flow rates for faster/slower operations
- Change temperature ranges for different climate conditions
- Modify operation durations and idle times

### Extending the Simulator

The simulator is designed with a modular architecture that can be extended:
- Add new product types
- Implement additional sensor types
- Create custom communication protocols
