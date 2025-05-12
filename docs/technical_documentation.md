# Refinery Tank Simulator Technical Documentation

## Architecture Overview

The Refinery Tank Simulator is built with a modular architecture that separates concerns into distinct components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Data Models    │     │   Simulators    │     │ Communication   │
│  - Tank         │◄────┤  - TankSim      │────►│  - MQTT Client  │
│  - Radar        │     │  - RadarSim     │     │  - Modbus Server│
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                       ▲
         │                      │                       │
         └──────────────┬──────┴───────────────┬───────┘
                        │                      │
                        ▼                      ▼
               ┌─────────────────┐    ┌─────────────────┐
               │  Configuration  │    │    Utilities    │
               │  - YAML Loader  │    │  - Logging      │
               └─────────────────┘    └─────────────────┘
```

## Component Descriptions

### 1. Data Models

#### Tank Model (`src/models/tank.py`)

The `Tank` class represents a physical tank in the refinery with properties:
- Static attributes (dimensions, product type, etc.)
- Dynamic state (level, volume, temperature, etc.)
- Strapping table for level-to-volume conversion
- Methods for updating state and calculating derived values

#### Radar Model (`src/models/radar.py`)

The `Radar` class simulates a SAAB radar sensor with:
- Configuration parameters (installation height, fine adjustment)
- Measurement functions with realistic error simulation
- Data conversion methods

#### Factory (`src/models/factory.py`)

The `TankFactory` class creates tanks and radars based on configuration:
- Generates tanks with realistic dimensions
- Creates corresponding radar for each tank
- Assigns unique identifiers and Modbus addresses

### 2. Simulators

#### Tank Simulator (`src/simulators/tank_simulator.py`)

The `TankSimulator` class handles the dynamic behavior of tanks:
- Simulates filling and draining operations
- Models fluid dynamics with realistic flow rates
- Updates temperatures based on product type
- Manages state transitions between operations

#### Radar Simulator (`src/simulators/radar_simulator.py`)

The `RadarSimulator` class simulates radar measurements:
- Calculates level readings with realistic errors
- Simulates temperature and pressure measurements
- Provides Modbus register interface
- Handles configuration updates

### 3. Communication

#### MQTT Client (`src/communication/mqtt_client.py`)

The `MQTTClient` class handles communication with ThingsBoard:
- Connects to MQTT broker
- Publishes telemetry data at configured intervals
- Sends static attributes
- Manages reconnection and error handling

#### Modbus Server (`src/communication/modbus_server.py`)

The `ModbusServer` class exposes radar data via Modbus RTU:
- Creates and manages Modbus register map
- Updates registers with current radar readings
- Processes register writes for configuration
- Generates ThingsBoard Gateway configuration

### 4. Configuration

The `ConfigLoader` class (`src/utils/config_loader.py`) manages configuration:
- Loads YAML configuration files
- Validates configuration structure
- Provides access to configuration parameters

### 5. Utilities

Utility modules provide supporting functionality:
- Logging setup and configuration
- Error handling and reporting

## Data Flow

1. **Initialization**:
   - Configuration is loaded from YAML files
   - Tanks and radars are created based on configuration
   - Communication components are initialized

2. **Simulation Cycle**:
   - Tank simulator updates tank states based on operations
   - Radar simulator calculates measurements from tank states
   - MQTT client publishes telemetry at configured intervals
   - Modbus server updates registers with current readings

3. **External Interaction**:
   - ThingsBoard receives telemetry via MQTT
   - ThingsBoard Gateway reads radar data via Modbus
   - Configuration changes can be written to Modbus registers

## Design Patterns

The simulator implements several design patterns:

1. **Factory Pattern**: The `TankFactory` creates tanks and radars
2. **Observer Pattern**: Simulators observe and react to state changes
3. **Facade Pattern**: The main application provides a simple interface to complex subsystems
4. **Strategy Pattern**: Different tank types implement different volume calculation strategies

## Performance Considerations

The simulator is designed to efficiently handle 131 tanks:

- Optimized update cycles with configurable intervals
- Efficient data structures for lookups (dictionaries instead of linear searches)
- Minimal memory footprint by sharing configuration
- Threaded communication to prevent blocking the main simulation loop

## Error Handling

The simulator implements comprehensive error handling:

- Exception catching and logging at all levels
- Graceful degradation (e.g., continuing without MQTT if connection fails)
- Signal handling for clean shutdown
- Detailed logging for troubleshooting

## Extension Points

The simulator can be extended in several ways:

1. **New Tank Types**: Add new tank type classes with specific behavior
2. **Additional Products**: Define new product types with properties
3. **Alternative Communication Protocols**: Implement new communication classes
4. **Custom Simulation Logic**: Extend or replace simulator classes

## Configuration Reference

See the comments in the YAML configuration files for detailed parameter descriptions:

- `simulation.yaml`: Simulation parameters
- `tanks.yaml`: Tank definitions
- `communication.yaml`: Communication settings

## Code Style and Conventions

The codebase follows these conventions:

- PEP 8 style guide for Python code
- Type hints for function parameters and return values
- Comprehensive docstrings in Google style
- Consistent error handling and logging
- Clear separation of concerns between modules
