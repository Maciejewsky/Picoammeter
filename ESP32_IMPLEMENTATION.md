# ESP32 + ADS1115 Integration - Implementation Summary

## Overview

This document summarizes the implementation of the ESP32 + ADS1115 integration feature for Keithley LabNano3D, enabling simultaneous measurements from VISA instruments and external sensors.

## Implementation Date
December 2, 2025

## Feature Description

The new "Instrumento + ESP32" mode allows users to:
- Connect both a VISA instrument (SMU 2450, Picoammeter 6487) and an ESP32 with ADS1115 ADC
- Perform simultaneous measurements from both sources
- Visualize data with dual Y-axis plots (VISA on left, ESP32/ADS1115 on right)
- Export data in CSV format with three columns: time, VISA reading, ESP32 reading
- Calibrate ADS1115 readings for various sensor types

## Architecture

### Core Components

1. **ESP32Manager** (`core/esp32_manager.py`)
   - Manages serial communication with ESP32 devices
   - Handles ADS1115 ADC readings via ESP32
   - Supports single-ended (A0-A3) and differential channels
   - Provides calibration system with raw/percentage modes

2. **ESP32ConnectionWidget** (`widgets/esp32_connection_widget.py`)
   - UI for connecting to ESP32 devices
   - Port scanning and device selection
   - Integrated calibration dialog with live readings
   - Support for multiple reading types and sensor calibration

3. **CombinedMeasurementWidget** (`widgets/combined_measurement_widget.py`)
   - Simultaneous data acquisition from VISA and ESP32
   - Dual Y-axis plotting using pyqtgraph
   - Configurable measurement intervals and duration
   - CSV export with comprehensive metadata

4. **ESP32 Firmware** (`firmware/esp32_ads1115.ino`)
   - Arduino sketch for ESP32
   - I2C communication with ADS1115
   - Serial protocol for PC communication
   - Support for all ADS1115 channels and gain settings

### UI Integration

- **ModeSelectionWidget**: Added "Instrumento + ESP32" button (orange)
- **InstrumentManagementWidget**: Added ESP32 tab (dynamically enabled in combined mode)
- **MainWindowV2**: Updated to handle combined mode state and widget creation

## Features

### ADS1115 Support

- **Channels**:
  - Single-ended: A0, A1, A2, A3 (relative to GND)
  - Differential: A0-A1, A0-A3, A2-A3, A1-A3

- **Gain Settings**: 6 programmable gain settings (±6.144V to ±0.256V)

- **Reading Types**:
  - Raw: 16-bit ADC values (0-32767)
  - Percentage: 0-100% calibrated scale

### Calibration System

- **Channel Selection**: Choose from 8 channels (4 single-ended + 4 differential)
- **Reading Type**: Select raw bits or percentage scale
- **Min/Max Calibration**: 
  - Set using live readings
  - Automatic inversion detection
  - Visual feedback for inverted sensors
- **Custom Labels**: Define sensor name and units

### Data Export

- **Format**: CSV with metadata header
- **Columns**:
  1. Time (s)
  2. VISA Reading (typically current in A)
  3. ESP32 Reading (calibrated value with unit)

- **Metadata Includes**:
  - User information
  - Timestamp
  - VISA parameters (voltage, compliance)
  - ESP32/ADS1115 configuration
  - Calibration settings

### Plotting

- **Dual Y-Axis**:
  - Left axis (blue): VISA instrument readings
  - Right axis (orange): ESP32/ADS1115 readings
- **Real-time Updates**: Both plots update simultaneously
- **Auto-scaling**: Each axis scales independently

## File Structure

```
keithley-labnano3d/
├── core/
│   └── esp32_manager.py          (NEW - ESP32 communication)
├── widgets/
│   ├── esp32_connection_widget.py    (NEW - ESP32 UI)
│   └── combined_measurement_widget.py (NEW - Combined measurements)
├── firmware/
│   ├── esp32_ads1115.ino         (NEW - Arduino firmware)
│   └── README.md                 (NEW - Firmware documentation)
├── main_window_v2.py             (MODIFIED - Combined mode support)
├── setup.py                      (MODIFIED - Added pyserial check)
├── README.md                     (MODIFIED - ESP32 documentation)
└── requirements.txt              (NEW - Dependencies list)
```

## Dependencies

- **New**: pyserial >= 3.5
- **Existing**: PyQt5, pyvisa, numpy, matplotlib, pyqtgraph

## Usage Workflow

1. **Hardware Setup**:
   - Upload firmware to ESP32
   - Connect ADS1115 to ESP32 (I2C)
   - Connect sensors to ADS1115
   - Connect ESP32 to PC via USB
   - Connect VISA instrument via USB/Ethernet

2. **Software Setup**:
   - Select "Instrumento + ESP32" mode
   - Connect VISA instrument (Real/Simulated tab)
   - Connect ESP32 (ESP32 tab)
   - Calibrate ADS1115 (⚙️ button)

3. **Measurement**:
   - Configure VISA parameters
   - Set measurement interval and duration
   - Start measurement
   - Observe dual plots in real-time
   - Export data when complete

## Debug Mode Support

- Debug mode is fully compatible with combined mode
- Allows simulated VISA instruments with real ESP32
- Useful for testing ESP32/sensor setup without VISA hardware

## Testing

### Syntax Validation
✅ All Python files compile without errors

### Integration Points
✅ Mode selection properly switches to combined mode
✅ ESP32 tab appears when combined mode is selected
✅ Calibration dialog opens and functions
✅ Combined measurement widget instantiates correctly

### Hardware Testing Required
- [ ] ESP32 firmware upload and communication
- [ ] ADS1115 readings via ESP32
- [ ] Calibration with actual sensors
- [ ] Simultaneous VISA + ESP32 measurements
- [ ] Data export verification

## Example Applications

1. **Environmental Monitoring During Electrical Characterization**
   - Measure device current while monitoring humidity
   - Track temperature effects on electrical properties
   - Correlate pressure changes with device behavior

2. **Soil Moisture + Ion Conductivity**
   - Simultaneous moisture and electrical conductivity
   - Agricultural research applications
   - Correlate water content with ion transport

3. **Multi-Parameter Sensor Arrays**
   - Up to 4 sensors simultaneously (using all ADS1115 channels)
   - Each sensor can have different calibration
   - Future expansion for 4 separate Y-axes

## Future Enhancements

As mentioned in the original issue, future work could include:

1. **Multi-Channel Support**:
   - Read all 4 ADS1115 channels simultaneously
   - Each channel with separate Y-axis and color
   - Individual calibration per channel

2. **Additional Reading Types**:
   - Temperature sensors (with linearization)
   - Pressure sensors
   - pH sensors
   - Custom transfer functions

3. **Advanced Calibration**:
   - Multi-point calibration (not just min/max)
   - Polynomial fitting for non-linear sensors
   - Temperature compensation

4. **Data Analysis**:
   - Cross-correlation between VISA and ESP32 readings
   - Automated anomaly detection
   - Statistical analysis tools

## Known Limitations

1. **Single ESP32 Device**: Currently supports one ESP32 at a time
2. **Single ADS1115 Channel**: Measurements use one channel at a time (future: simultaneous multi-channel)
3. **Fixed Sampling Rate**: Limited by serial communication overhead
4. **No Real-Time Filtering**: Raw ADC values are used (future: moving average, etc.)

## Conclusion

The ESP32 + ADS1115 integration is fully implemented and ready for testing with actual hardware. The modular design allows for easy extension and maintenance, and the comprehensive documentation ensures users can quickly set up and use the system.

All code has been validated for syntax errors and follows the existing code style of the project. The integration seamlessly fits into the existing architecture without breaking any existing functionality.
