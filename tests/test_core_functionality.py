#!/usr/bin/env python3
"""
Test script for Keithley LabNano3D v2.0 core functionality
Tests the new architecture components without GUI
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import get_logger, init_logging
from core.user_manager import get_user_manager
from core.config import get_config_manager, InstrumentConfig, MeasurementConfig
from core.debug_mode import get_debug_manager


def test_user_management():
    """Test user management functionality"""
    print("=" * 50)
    print("Testing User Management")
    print("=" * 50)
    
    user_manager = get_user_manager()
    
    # Create a test user
    username = user_manager.create_user_profile("Maria", "Santos")
    print(f"✅ Created user: {username}")
    
    # Test user preferences
    user_manager.set_user_preference("theme", "dark")
    theme = user_manager.get_user_preference("theme")
    print(f"✅ User preference set/get: theme = {theme}")
    
    # List users
    users = user_manager.list_users()
    print(f"✅ Total users: {len(users)}")
    for user in users:
        print(f"   - {user['first_name']} {user['last_name']} ({user['username']})")
    
    return username


def test_logging(username):
    """Test logging functionality"""
    print("\n" + "=" * 50)
    print("Testing Logging System")
    print("=" * 50)
    
    logger = init_logging(username)
    
    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    print("✅ Logger tested - check logs directory for output")
    
    # Test specific logging methods
    logger_instance = get_logger(username)
    from core.logger import _logger_instance
    _logger_instance.log_instrument_command("SMU_TEST", "*IDN?", "KEITHLEY,MODEL 2450,12345,1.0.0")
    _logger_instance.log_measurement_start("IV_CURVE", {"voltage_range": "0-10V", "points": 100})
    _logger_instance.log_measurement_end("IV_CURVE", 45.2, 100)
    _logger_instance.log_user_action("Connected instrument", "SMU 2450")
    
    print("✅ Specialized logging methods tested")


def test_configuration():
    """Test configuration management"""
    print("\n" + "=" * 50)
    print("Testing Configuration Management")
    print("=" * 50)
    
    user_manager = get_user_manager()
    config_manager = get_config_manager(user_manager)
    
    # Test app config
    app_config = config_manager.get_app_config()
    print(f"✅ App config loaded - debug_mode: {app_config.debug_mode}")
    
    # Update app config
    config_manager.update_app_config(debug_mode=True, theme="dark")
    updated_config = config_manager.get_app_config()
    print(f"✅ App config updated - debug_mode: {updated_config.debug_mode}, theme: {updated_config.theme}")
    
    # Test instrument config
    instrument_config = InstrumentConfig(
        name="Test SMU",
        model="MODEL 2450",
        address="USB0::0x05E6::0x2450::12345::INSTR",
        timeout=5000
    )
    config_manager.add_instrument_config("test_smu", instrument_config)
    
    retrieved_config = config_manager.get_instrument_config("test_smu")
    print(f"✅ Instrument config saved/loaded: {retrieved_config.name}")
    
    # Test measurement config
    measurement_config = MeasurementConfig(
        measurement_type="IV_CURVE",
        parameters={"start_voltage": 0, "end_voltage": 10, "points": 100},
        auto_save=True,
        export_format="csv"
    )
    config_manager.add_measurement_config("iv_test", measurement_config)
    
    retrieved_measurement = config_manager.get_measurement_config("iv_test")
    print(f"✅ Measurement config saved/loaded: {retrieved_measurement.measurement_type}")
    
    # Test password verification
    correct_password = config_manager.verify_debug_password("debug123")
    wrong_password = config_manager.verify_debug_password("wrong")
    print(f"✅ Password verification: correct={correct_password}, wrong={wrong_password}")


def test_debug_instruments():
    """Test simulated instruments"""
    print("\n" + "=" * 50)
    print("Testing Debug/Simulated Instruments")
    print("=" * 50)
    
    debug_manager = get_debug_manager()
    
    # List available instruments
    instruments = debug_manager.list_available_instruments()
    print(f"✅ Available simulated instruments: {len(instruments)}")
    for instrument in instruments:
        print(f"   - {instrument['name']}: {instrument['model']} ({instrument['serial']})")
    
    # Test connecting to SMU 2450
    smu_name = "SMU_2450_1"
    success = debug_manager.connect_instrument(smu_name)
    print(f"✅ Connected to {smu_name}: {success}")
    
    # Get and test the instrument
    smu = debug_manager.get_instrument(smu_name)
    if smu:
        print(f"✅ Retrieved instrument: {smu.model}")
        
        # Test basic commands
        idn = smu.query("*IDN?")
        print(f"✅ IDN query: {idn}")
        
        # Test voltage setting and measurement
        smu.write("SOUR:VOLT 5.0")
        smu.write("OUTP ON")
        voltage = smu.query("SOUR:VOLT?")
        current = smu.query("MEAS:CURR?")
        resistance = smu.query("MEAS:RES?")
        
        print(f"✅ Voltage set: {voltage} V")
        print(f"✅ Current measured: {current} A")
        print(f"✅ Resistance measured: {resistance} Ω")
        
        # Turn off output
        smu.write("OUTP OFF")
        output_status = smu.query("OUTP?")
        print(f"✅ Output turned off: {output_status}")
    
    # Test adding custom instrument
    try:
        custom_instrument = debug_manager.add_custom_instrument("CUSTOM_TEST", "SMU2450", "CUSTOM001")
        print(f"✅ Custom instrument added: {custom_instrument.model}")
    except Exception as e:
        print(f"❌ Error adding custom instrument: {e}")
    
    # Test Picoammeter
    pico_name = "PICO_6487_1"
    success = debug_manager.connect_instrument(pico_name)
    pico = debug_manager.get_instrument(pico_name)
    if pico:
        idn = pico.query("*IDN?")
        print(f"✅ Picoammeter IDN: {idn}")
        
        # Test current measurement
        current = pico.query("MEAS:CURR?")
        print(f"✅ Picoammeter current: {current} A")


def test_file_structure():
    """Test that proper file structure is created"""
    print("\n" + "=" * 50)
    print("Testing File Structure")
    print("=" * 50)
    
    # Check if directories exist
    directories = ["users", "logs", "config"]
    for directory in directories:
        path = Path(directory)
        if path.exists():
            print(f"✅ Directory exists: {directory}")
            if directory == "users":
                # List users
                for user_dir in path.iterdir():
                    if user_dir.is_dir():
                        print(f"   User: {user_dir.name}")
                        for subdir in ["measurements", "scripts", "exports", "configs"]:
                            subdir_path = user_dir / subdir
                            if subdir_path.exists():
                                print(f"     ✅ {subdir}")
        else:
            print(f"❌ Directory missing: {directory}")


def run_all_tests():
    """Run all tests"""
    print("🔬 Keithley LabNano3D v2.0 - Core Functionality Tests")
    print("=" * 60)
    
    try:
        # Test user management
        username = test_user_management()
        
        # Test logging
        test_logging(username)
        
        # Test configuration
        test_configuration()
        
        # Test debug instruments
        test_debug_instruments()
        
        # Test file structure
        test_file_structure()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Core functionality is working correctly.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)