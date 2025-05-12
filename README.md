# Refinery Tank Simulator with ThingsBoard Integration

A comprehensive Python-based simulator that models the behavior of 131 refinery tanks across 4 patios, their SAAB radar sensors, and integrates with ThingsBoard through MQTT and Modbus RTU protocols.

## Overview

This simulator was developed to serve as a testing platform for ThingsBoard implementation as a replacement for the Tankmaster system in refineries. It provides realistic simulation of tank operations, fluid dynamics, and sensor readings that can be used to validate ThingsBoard configurations and dashboards.

## Features

- **Realistic Tank Simulation**:
  - 131 tanks across 4 refinery patios (Cerro de Carga, Osanco, Chaure, Refinería)
  - Accurate physical dimensions and capacities
  - Strapping tables for level-to-volume conversion
  - Dynamic filling and draining operations
  - Product-specific temperature and pressure modeling

- **SAAB Radar Simulation**:
  - Realistic level measurement with configurable error margins
  - Multiple temperature sensors per tank
  - Pressure readings
  - Configurable installation parameters

- **ThingsBoard Integration**:
  - Direct MQTT communication for tank telemetry
  - Modbus RTU server for radar sensor data
  - Automatic generation of ThingsBoard Gateway configurations
  - Bidirectional communication for radar configuration

- **Advanced Features**:
  - Configurable through YAML files
  - Comprehensive logging and error handling
  - Visualization tools for tank status and history
  - Docker support for easy deployment

## Project Structure

```
refinery-tank-simulator/
├── config/                  # Configuration files
│   ├── communication.yaml   # MQTT and Modbus settings
│   ├── simulation.yaml      # Simulation parameters
│   └── tanks.yaml           # Tank definitions
├── docs/                    # Documentation
│   ├── technical_documentation.md
│   ├── thingsboard_integration.md
│   └── user_manual.md
├── src/                     # Source code
│   ├── communication/       # MQTT and Modbus interfaces
│   ├── models/              # Data models for tanks and radars
│   ├── simulators/          # Simulation logic
│   ├── utils/               # Utility functions
│   └── main.py              # Main application entry point
├── thingsboard_gateway/     # ThingsBoard Gateway configurations
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose for simulator and ThingsBoard
└── requirements.txt         # Python dependencies
```

## Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/refinery-tank-simulator.git
   cd refinery-tank-simulator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the simulator:
   ```bash
   python src/main.py
   ```

### Docker Deployment

For easier deployment with ThingsBoard:

```bash
docker-compose up -d
```

This will start:
- The tank simulator
- ThingsBoard Community Edition
- ThingsBoard Gateway with the simulator's configurations

## Configuration

The simulator is configured through YAML files in the `config/` directory:

### tanks.yaml

Defines the physical properties of tanks:
- Patio distributions and tank counts
- Size ranges and product types
- Tank type characteristics (standard, floating roof, conical bottom)

### simulation.yaml

Controls the simulation behavior:
- Update intervals
- Flow rates for different products
- Temperature ranges
- Radar simulation parameters

### communication.yaml

Configures communication protocols:
- MQTT broker settings for ThingsBoard
- Modbus server configuration
- Register mappings

## Utility Tools

The simulator includes several utility tools:

- **Data Generator**: Creates sample tank data for testing
  ```bash
  python src/utils/data_generator.py --history --days 7
  ```

- **Visualization**: Visualizes tank levels and states
  ```bash
  python src/utils/visualization.py --data-file data/sample_data.json
  ```

- **Modbus Test**: Tests Modbus communication
  ```bash
  python src/utils/modbus_test.py --action read --address 1 --monitor
  ```

- **MQTT Test**: Tests MQTT communication with ThingsBoard
  ```bash
  python src/utils/mqtt_test.py --action subscribe
  ```

- **Gateway Config Generator**: Generates ThingsBoard Gateway configurations
  ```bash
  python src/utils/gateway_config_generator.py
  ```

## Documentation

Detailed documentation is available in the `docs/` directory:

- [User Manual](docs/user_manual.md): Instructions for using the simulator
- [Technical Documentation](docs/technical_documentation.md): Architecture and design details
- [ThingsBoard Integration](docs/thingsboard_integration.md): Guide for integrating with ThingsBoard

## License

MIT

## Author

Created for refinery monitoring and control systems modernization projects.

