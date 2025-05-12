# ThingsBoard Integration Guide

This document provides detailed instructions for integrating the Refinery Tank Simulator with ThingsBoard IoT Platform.

## Overview

The simulator integrates with ThingsBoard in two ways:

1. **Direct MQTT Communication**: Tank data is sent directly to ThingsBoard via MQTT
2. **Modbus RTU via ThingsBoard Gateway**: Radar sensor data is exposed via Modbus RTU and accessed through ThingsBoard Gateway

## Prerequisites

- ThingsBoard CE/PE installed and running
- ThingsBoard IoT Gateway installed and configured
- Basic understanding of ThingsBoard concepts (Devices, Assets, Dashboards)

## ThingsBoard Data Model

We recommend the following asset hierarchy in ThingsBoard:

```
Refinery
├── Cerro de Carga (Patio)
│   ├── CRG-TK-01 (Tank)
│   │   └── Radar (Device)
│   ├── CRG-TK-02 (Tank)
│   │   └── Radar (Device)
│   └── ...
├── Osanco (Patio)
│   ├── OSA-TK-01 (Tank)
│   │   └── Radar (Device)
│   └── ...
├── Chaure (Patio)
│   ├── CHR-TK-01 (Tank)
│   │   └── Radar (Device)
│   └── ...
└── Refinería (Patio)
    ├── REF-TK-01 (Tank)
    │   └── Radar (Device)
    └── ...
```

## Direct MQTT Integration

### Configuration

1. In ThingsBoard, create devices for each tank with the device name matching the tank ID (e.g., "CRG-TK-01")
2. Configure the simulator's `communication.yaml` file with your ThingsBoard MQTT broker details:

```yaml
mqtt:
  broker: "your-thingsboard-host"
  port: 1883
  client_id: "tank_simulator"
  username: "your-access-token"  # Device access token from ThingsBoard
  password: ""  # Leave empty if using access token as username
```

### Data Format

The simulator sends the following data to ThingsBoard:

#### Attributes (Static Data)

```json
{
  "id": "CRG-TK-01",
  "patio": "Cerro de Carga",
  "product": "crudo",
  "height": 15.2,
  "diameter": 45.6,
  "capacity": 120000,
  "tank_type": "standard",
  "strapping_table": { "0": 0, "1": 10.5, ... }
}
```

#### Telemetry (Dynamic Data)

```json
{
  "level": 10250.5,
  "volume": 85420.3,
  "fill_percentage": 71.2,
  "state": "filling",
  "temperatures": [65.2, 64.8, 63.5, 62.9, 61.7, 60.2],
  "average_temperature": 63.05,
  "pressure": 105.2
}
```

## ThingsBoard Gateway Integration for Modbus

### Configuration

The simulator generates ThingsBoard Gateway configuration files in the `thingsboard_gateway` directory:

1. Copy `modbus_mapping.json` to your ThingsBoard Gateway's configuration directory
2. Update the Gateway's main configuration to include the Modbus extension
3. Restart the ThingsBoard Gateway service

### Modbus Register Map

Each radar device has the following register map:

| Register Name | Offset | Data Type | Access | Description |
|---------------|--------|-----------|--------|-------------|
| level | 0 | UINT32 | Read | Level in mm from bottom |
| temperature_1 | 1 | INT16 | Read | Temperature sensor 1 (°C × 10) |
| temperature_2 | 2 | INT16 | Read | Temperature sensor 2 (°C × 10) |
| temperature_3 | 3 | INT16 | Read | Temperature sensor 3 (°C × 10) |
| temperature_4 | 4 | INT16 | Read | Temperature sensor 4 (°C × 10) |
| temperature_5 | 5 | INT16 | Read | Temperature sensor 5 (°C × 10) |
| temperature_6 | 6 | INT16 | Read | Temperature sensor 6 (°C × 10) |
| pressure | 7 | UINT16 | Read | Pressure (kPa × 100) |
| radar_height | 8 | UINT32 | Read/Write | Radar installation height (mm) |
| fine_adjustment | 9 | INT16 | Read/Write | Fine adjustment offset (mm × 10) |

The base address for each tank is calculated as:
```
tank_base_address + ((modbus_address - 1) * registers_per_tank)
```

Where:
- `tank_base_address` is 1000 (default)
- `modbus_address` is the unique Modbus address of the radar (starting from 1)
- `registers_per_tank` is 20 (default)

For example, the level register for radar with Modbus address 1 would be at address 1000.

## Creating ThingsBoard Dashboards

We recommend creating the following dashboards:

1. **Refinery Overview**: Shows all patios with summary statistics
2. **Patio View**: Detailed view of all tanks in a specific patio
3. **Tank Details**: Comprehensive view of a single tank with all its parameters
4. **Radar Configuration**: Interface for configuring radar parameters

### Example Widgets for Tank Details Dashboard

- **Tank Level Indicator**: Vertical bar showing current level and capacity
- **Product Information**: Card showing product type and properties
- **Temperature Chart**: Line chart showing all temperature sensors
- **Operation Status**: Card showing current state (filling, draining, idle)
- **Historical Data**: Time-series chart showing level and volume over time

## Alarm Configuration

We recommend configuring the following alarms in ThingsBoard:

1. **High Level Alarm**: When tank level exceeds 90% of capacity
2. **Low Level Alarm**: When tank level falls below 10% of capacity
3. **High Temperature Alarm**: Product-specific temperature thresholds
4. **Rapid Level Change**: Detect unusual filling or draining rates
5. **Communication Loss**: When telemetry stops being received

## Rule Chains

Create rule chains to:

1. Route data to the appropriate dashboard
2. Process level changes to calculate flow rates
3. Detect and alert on abnormal conditions
4. Archive historical data for reporting

## Advanced Integration

For advanced integration scenarios:

1. **REST API**: Use ThingsBoard's REST API to pull data into external systems
2. **Data Export**: Configure data export to external databases for long-term storage
3. **Custom Widgets**: Develop custom widgets for specialized visualizations
4. **Mobile App**: Use ThingsBoard Mobile Application for on-the-go monitoring
