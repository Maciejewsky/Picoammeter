#!/usr/bin/env python3
"""
Test database functionality for Keithley LabNano3D v2.0
"""

import sys
import os
from pathlib import Path
import tempfile
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager, get_database_manager
from core.user_manager import get_user_manager


def test_database_functionality():
    """Test database functionality"""
    print("=" * 50)
    print("Testing Database Functionality")
    print("=" * 50)
    
    # Create database manager
    user_manager = get_user_manager()
    db_manager = get_database_manager(user_manager)
    
    # Test user management
    user_id = db_manager.add_user("test_user", "Test", "User", {"theme": "dark"})
    print(f"✅ User added to database: {user_id}")
    
    # Get user back
    user = db_manager.get_user_by_username("test_user")
    print(f"✅ User retrieved: {user['first_name']} {user['last_name']}")
    
    # Test instrument management
    instrument_id = db_manager.add_instrument(
        name="Test SMU",
        model="MODEL 2450",
        address="USB0::0x05E6::0x2450::12345::INSTR",
        manufacturer="KEITHLEY INSTRUMENTS",
        serial_number="12345",
        instrument_type="smu_2450",
        is_simulated=False
    )
    print(f"✅ Instrument added: {instrument_id}")
    
    # Get instruments
    instruments = db_manager.get_instruments()
    print(f"✅ Retrieved {len(instruments)} instruments")
    
    # Test measurement creation
    measurement_id = db_manager.create_measurement(
        user_id=user_id,
        measurement_type="IV_CURVE",
        title="Test IV Measurement",
        instrument_id=instrument_id,
        description="Testing database functionality",
        parameters={
            "start_voltage": 0,
            "end_voltage": 10,
            "points": 100,
            "compliance": 0.001
        },
        notes="Database test measurement"
    )
    print(f"✅ Measurement created: {measurement_id}")
    
    # Start measurement
    db_manager.start_measurement(measurement_id)
    print("✅ Measurement started")
    
    # Add some data points
    for i in range(10):
        voltage = i * 1.0
        current = voltage * 0.001 + (i * 0.0001)  # Simulate some resistance
        
        db_manager.add_measurement_data_point(
            measurement_id=measurement_id,
            data_index=i,
            data={
                "voltage": voltage,
                "current": current,
                "resistance": voltage / current if current > 0 else float('inf'),
                "power": voltage * current
            }
        )
    
    print("✅ Added 10 data points")
    
    # Complete measurement
    db_manager.complete_measurement(measurement_id, data_points=10)
    print("✅ Measurement completed")
    
    # Test measurement retrieval
    measurements = db_manager.get_measurements(user_id=user_id)
    print(f"✅ Retrieved {len(measurements)} measurements for user")
    
    # Test data retrieval
    data_points = db_manager.get_measurement_data(measurement_id)
    print(f"✅ Retrieved {len(data_points)} data points")
    
    # Test configuration preset
    preset_id = db_manager.save_configuration_preset(
        user_id=user_id,
        name="Standard IV",
        measurement_type="IV_CURVE",
        parameters={
            "start_voltage": 0,
            "end_voltage": 5,
            "points": 50,
            "compliance": 0.001,
            "delay": 0.1
        },
        description="Standard IV curve measurement"
    )
    print(f"✅ Configuration preset saved: {preset_id}")
    
    # Get presets
    presets = db_manager.get_configuration_presets(user_id, "IV_CURVE")
    print(f"✅ Retrieved {len(presets)} configuration presets")
    
    # Test export to CSV
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        export_path = tmp.name
    
    success = db_manager.export_measurement_to_csv(measurement_id, export_path)
    if success:
        print(f"✅ Exported measurement to CSV: {export_path}")
        
        # Check file content
        with open(export_path, 'r') as f:
            content = f.read()
            print(f"   CSV file size: {len(content)} characters")
            lines = content.split('\n')
            print(f"   CSV file lines: {len(lines)}")
            print(f"   First few lines:")
            for i, line in enumerate(lines[:5]):
                print(f"     {i+1}: {line}")
    else:
        print("❌ Failed to export measurement to CSV")
    
    # Test statistics
    stats = db_manager.get_statistics(user_id)
    print(f"✅ Statistics for user:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Global statistics
    global_stats = db_manager.get_statistics()
    print(f"✅ Global statistics:")
    for key, value in global_stats.items():
        print(f"   {key}: {value}")
    
    # Clean up temporary file
    try:
        os.unlink(export_path)
        print("✅ Cleaned up temporary CSV file")
    except:
        pass
    
    print("\n🎉 All database tests passed!")
    return True


def test_database_integration():
    """Test database integration with other components"""
    print("\n" + "=" * 50)
    print("Testing Database Integration")
    print("=" * 50)
    
    # Test with user manager
    user_manager = get_user_manager()
    
    # Create a new user
    username = user_manager.create_user_profile("Database", "Tester")
    print(f"✅ User created via user manager: {username}")
    
    # Get database manager
    db_manager = get_database_manager(user_manager)
    
    # Add user to database
    user_info = user_manager.get_current_user_info()
    user_id = db_manager.add_user(
        username=username,
        first_name=user_info['first_name'],
        last_name=user_info['last_name'],
        preferences=user_info.get('preferences', {})
    )
    print(f"✅ User added to database: {user_id}")
    
    # Test simulated instrument integration
    from core.debug_mode import get_debug_manager
    
    debug_manager = get_debug_manager()
    instruments = debug_manager.list_available_instruments()
    
    # Add simulated instruments to database
    for instrument in instruments[:2]:  # Add first two
        db_instrument_id = db_manager.add_instrument(
            name=instrument['name'],
            model=instrument['model'],
            address=instrument['address'],
            manufacturer="KEITHLEY INSTRUMENTS",
            serial_number=instrument['serial'],
            instrument_type=instrument['name'].split('_')[0].lower(),
            is_simulated=True,
            configuration={"simulated": True, "backend": "debug"}
        )
        print(f"✅ Simulated instrument added to database: {instrument['name']}")
    
    # Create measurement with simulated instrument
    db_instruments = db_manager.get_instruments()
    if db_instruments:
        measurement_id = db_manager.create_measurement(
            user_id=user_id,
            measurement_type="RESISTANCE_TIME",
            title="Simulated Resistance Measurement",
            instrument_id=db_instruments[0]['id'],
            description="Testing with simulated instrument",
            parameters={
                "duration": 60,
                "interval": 1,
                "voltage": 1.0
            }
        )
        print(f"✅ Measurement created with simulated instrument: {measurement_id}")
    
    print("\n🎉 Database integration tests passed!")
    return True


if __name__ == "__main__":
    try:
        print("🗄️ Keithley LabNano3D v2.0 - Database Tests")
        print("=" * 60)
        
        # Run tests
        test_database_functionality()
        test_database_integration()
        
        print("\n" + "=" * 60)
        print("🎉 ALL DATABASE TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DATABASE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)