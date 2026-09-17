# Keithley LabNano3D v2.0 - Architecture Documentation

## 🎯 Overview

Keithley LabNano3D v2.0 represents a complete architectural restructuring of the instrument control application, implementing all requested features from the modernization requirements while maintaining backward compatibility with Keithley SMU 2450 and Picoammeter 6487 instruments.

## 🏗️ New Architecture

### Core Components

#### 1. User Management (`core/user_manager.py`)
- **Purpose**: Manages user profiles and data organization
- **Features**:
  - User registration with first name and last name
  - Dedicated directories for each user (measurements, scripts, exports, configs)
  - User preferences and session management
  - Automatic directory structure creation

#### 2. Logging System (`core/logger.py`)
- **Purpose**: Comprehensive logging with user-specific organization
- **Features**:
  - User-specific log files with rotation
  - Specialized logging for instrument commands, measurements, and user actions
  - Multiple log levels (DEBUG, INFO, WARNING, ERROR)
  - File and console output with different formatting

#### 3. Configuration Management (`core/config.py`)
- **Purpose**: Centralized configuration for application, instruments, and measurements
- **Features**:
  - Application-wide settings (debug mode, themes, etc.)
  - Instrument-specific configurations with auto-reconnect
  - Measurement parameter presets
  - User-specific preference overrides

#### 4. Debug Mode (`core/debug_mode.py`)
- **Purpose**: Simulated instruments for testing and development
- **Features**:
  - Password-protected debug mode activation
  - Realistic simulation of SMU 2450 and Picoammeter 6487
  - Customizable simulated instrument creation
  - SCPI command compatibility for testing

#### 5. Database System (`core/database.py`)
- **Purpose**: Local SQLite database for data persistence
- **Features**:
  - Complete measurement history storage
  - User and instrument management
  - Configuration presets
  - Data export with metadata
  - Statistical analysis and reporting

#### 6. Script Management (`core/script_manager.py`)
- **Purpose**: Custom measurement script creation and execution
- **Features**:
  - Built-in measurement scripts (IV curves, resistance vs time, automated sequences)
  - User script creation, editing, and management
  - Script import/export functionality
  - Parameter validation and type checking
  - Safe script execution environment

### User Interface Components

#### 1. Startup Window (`startup_window.py`)
- **Purpose**: Modern user login and application initialization
- **Features**:
  - User registration and login interface
  - Debug mode activation with password
  - Modern, responsive design
  - User preference loading

#### 2. Main Window v2 (`main_window_v2.py`)
- **Purpose**: Main application interface with inactive start state
- **Features**:
  - Inactive welcome screen with connect/load options
  - Multi-instrument support in single window
  - Manual command console for direct SCPI communication
  - Instrument status monitoring
  - Modern tabbed interface for measurements

#### 3. Connection Window v2 (`connection_window_v2.py`)
- **Purpose**: Enhanced instrument connection interface
- **Features**:
  - Real instrument scanning and identification
  - Simulated instrument selection (debug mode)
  - Automatic instrument type detection
  - Connection status monitoring

## 📊 Built-in Measurement Scripts

### 1. IV Curve Measurement (`scripts/builtin/iv_curve.py`)
- **Purpose**: Voltage sweep with current measurement
- **Parameters**: Start/end voltage, points, compliance, delay
- **Output**: Voltage, current, resistance, power vs point

### 2. Resistance vs Time (`scripts/builtin/resistance_time.py`)
- **Purpose**: Time-based resistance monitoring
- **Parameters**: Test voltage, duration, interval, compliance
- **Output**: Time-series resistance data

### 3. Automated Sequence (`scripts/builtin/automated_sequence.py`)
- **Purpose**: Combined resistance stability + IV curve measurement
- **Parameters**: Resistance phase settings, rest time, IV curve settings
- **Output**: Structured data with both measurement phases

## 🗄️ Database Schema

### Tables
- **users**: User profiles and preferences
- **instruments**: Connected instrument information
- **measurements**: Measurement metadata and parameters
- **measurement_data**: Actual measurement data points
- **configuration_presets**: Saved measurement configurations
- **exported_files**: Export operation tracking

### Features
- Foreign key constraints for data integrity
- Automatic indexing for performance
- Comprehensive metadata storage
- Export functionality with CSV format

## 🔧 Installation and Setup

### Prerequisites
- Python 3.8 or higher
- PyQt5 for GUI (optional - console mode available)
- VISA drivers for real instruments (optional - debug mode available)

### Installation
```bash
# Clone repository
git clone https://github.com/LucJBQ/keithley-labnano3d.git
cd keithley-labnano3d

# Install dependencies
pip install -r requirements.txt

# Run application
python main_v2.py
```

### Testing
```bash
# Test core functionality
python test_core_functionality.py

# Test database system
python test_database.py

# Test script manager
python test_script_manager.py

# Complete integration test
python test_integration.py
```

## 🚀 Usage

### 1. First Run
1. Launch application: `python main_v2.py`
2. Enter first name and last name to create user profile
3. Choose to activate debug mode for testing (password: `debug123`)
4. Application opens with inactive welcome screen

### 2. Connecting Instruments
1. Click "Conectar Instrumento" button
2. In real mode: Scan for VISA instruments
3. In debug mode: Select from simulated instruments
4. Multiple instruments can be connected simultaneously

### 3. Running Measurements
1. Select instrument and measurement type
2. Configure parameters using built-in or custom scripts
3. Execute measurement with real-time monitoring
4. Data automatically saved to database

### 4. Manual Commands
1. Use command console in left panel
2. Select target instrument
3. Send SCPI commands directly (e.g., `*IDN?`, `SOUR:VOLT 5.0`)
4. View responses in console output

### 5. Data Management
1. All measurements automatically saved to database
2. Export to CSV with complete metadata
3. Load previous measurements from database
4. Save/load configuration presets

## 🔬 Debug Mode Features

### Simulated Instruments
- **SMU 2450**: Realistic voltage/current simulation with noise
- **Picoammeter 6487**: Ultra-low current simulation
- **Custom Instruments**: Create additional simulated devices

### Testing Capabilities
- Complete measurement workflows without hardware
- Script development and validation
- User interface testing
- Database and export functionality validation

## 📈 Script Development

### Creating Custom Scripts
1. Navigate to user scripts directory: `users/{username}/scripts/`
2. Create Python file with required functions:
   - `execute_measurement(instrument, parameters, logger)`
   - `get_parameter_definitions()` (optional)
3. Use script manager to validate and test

### Script Requirements
```python
def execute_measurement(instrument, parameters, logger=None):
    """
    Main measurement execution function
    
    Args:
        instrument: Connected instrument object
        parameters: Dictionary of measurement parameters
        logger: Optional logger for status updates
    
    Returns:
        List of measurement data dictionaries
    """
    # Your measurement code here
    pass

def get_parameter_definitions():
    """
    Return parameter definitions for UI generation
    
    Returns:
        Dictionary mapping parameter names to definitions
    """
    return {
        'voltage': {
            'type': 'float',
            'default': 1.0,
            'min': 0.0,
            'max': 10.0,
            'unit': 'V',
            'description': 'Test voltage'
        }
    }
```

## 🔒 Security and Data Management

### User Data Isolation
- Each user has dedicated directories
- Database entries linked to specific users
- Configuration and preferences stored per user

### Password Protection
- Debug mode requires password authentication
- Configurable password in application settings
- Prevents accidental activation of test mode

### Data Backup
- All data stored in local SQLite database
- User directories contain file-based backups
- Export functionality for data migration

## 🧪 Testing Framework

### Test Coverage
- **Core Functionality**: User management, logging, configuration
- **Database Operations**: CRUD operations, exports, statistics
- **Script Execution**: Built-in and custom script validation
- **Integration**: Complete workflow testing

### Test Files
- `test_core_functionality.py`: Core component testing
- `test_database.py`: Database functionality validation
- `test_script_manager.py`: Script system testing
- `test_integration.py`: End-to-end workflow testing

## 🛠️ Development Guidelines

### Adding New Instruments
1. Create instrument class in `core/debug_mode.py` (for simulation)
2. Add detection logic in `connection_window_v2.py`
3. Create instrument-specific widgets in `widgets/{instrument}/`
4. Update main window to handle new instrument type

### Creating New Measurement Types
1. Add script template to `scripts/builtin/`
2. Update database schema if needed for specific data structures
3. Create UI widgets for parameter configuration
4. Add export format support if required

### Extending Export Formats
1. Add export function to `core/database.py`
2. Update measurement record tracking
3. Add format selection to UI
4. Implement format-specific metadata handling

## 🔮 Future Enhancements

### Planned Features
- Enhanced graphing with pyqtgraph
- Origin file format compatibility
- Network instrument support
- Advanced data analysis tools
- Report generation system
- Web interface for remote access

### Architecture Ready For
- Plugin system for third-party instruments
- Distributed measurement coordination
- Cloud data synchronization
- Advanced scripting with Python packages
- Real-time collaboration features

## 📝 Migration from v1.0

### Compatibility
- Original instrument support maintained
- Existing measurement workflows supported
- Data can be imported from old formats

### New Features Available
- User-based data organization
- Comprehensive logging and history
- Script-based measurement automation
- Database storage and export
- Debug mode for development
- Modern, responsive interface

---

*This architecture provides a solid foundation for advanced laboratory instrument control with modern software engineering practices.*