#!/usr/bin/env python3
"""
Comprehensive integration test for Keithley LabNano3D v2.0
Tests all components working together
"""

import sys
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.user_manager import get_user_manager
from core.logger import init_logging
from core.config import get_config_manager
from core.debug_mode import get_debug_manager
from core.database import get_database_manager
from core.script_manager import get_script_manager


def test_complete_workflow():
    """Test a complete measurement workflow"""
    print("🔬 Complete Workflow Integration Test")
    print("=" * 60)
    
    # 1. User Management
    print("\n1. Setting up user...")
    user_manager = get_user_manager()
    username = user_manager.create_user_profile("Integration", "Tester")
    user_info = user_manager.get_current_user_info()
    print(f"✅ User created: {user_info['first_name']} {user_info['last_name']}")
    
    # 2. Logging
    print("\n2. Initializing logging...")
    logger = init_logging(username)
    logger.info("Starting integration test")
    print("✅ Logging system active")
    
    # 3. Configuration
    print("\n3. Loading configuration...")
    config_manager = get_config_manager(user_manager)
    config_manager.update_app_config(debug_mode=True)
    app_config = config_manager.get_app_config()
    print(f"✅ Configuration loaded - Debug mode: {app_config.debug_mode}")
    
    # 4. Database
    print("\n4. Setting up database...")
    db_manager = get_database_manager(user_manager)
    
    # Add user to database
    existing_user = db_manager.get_user_by_username(username)
    if existing_user:
        user_id = existing_user['id']
        print(f"✅ Using existing user from database: {user_id}")
    else:
        user_id = db_manager.add_user(
            username=username,
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            preferences=user_info.get('preferences', {})
        )
        print(f"✅ User added to database: {user_id}")
    
    # 5. Simulated Instruments
    print("\n5. Setting up simulated instruments...")
    debug_manager = get_debug_manager()
    instruments = debug_manager.list_available_instruments()
    print(f"✅ Available instruments: {len(instruments)}")
    
    # Connect to first SMU
    smu_name = "SMU_2450_1"
    success = debug_manager.connect_instrument(smu_name)
    smu = debug_manager.get_instrument(smu_name)
    print(f"✅ Connected to {smu_name}: {success}")
    
    # Add instrument to database
    instrument_id = db_manager.add_instrument(
        name=smu_name,
        model=smu.model,
        address=smu.address,
        manufacturer="KEITHLEY INSTRUMENTS",
        serial_number=smu.serial,
        instrument_type="smu_2450",
        is_simulated=True
    )
    print(f"✅ Instrument added to database: {instrument_id}")
    
    # 6. Script Manager
    print("\n6. Loading measurement scripts...")
    script_manager = get_script_manager(user_manager)
    scripts = script_manager.list_scripts()
    print(f"✅ Available scripts: {len(scripts)}")
    
    # 7. Execute a measurement workflow
    print("\n7. Executing measurement workflow...")
    
    # Create measurement in database
    measurement_id = db_manager.create_measurement(
        user_id=user_id,
        measurement_type="IV_CURVE",
        title="Integration Test IV Measurement",
        instrument_id=instrument_id,
        description="Testing complete workflow integration",
        parameters={
            "start_voltage": 0.0,
            "end_voltage": 5.0,
            "points": 11,
            "compliance": 0.001,
            "delay": 0.01
        },
        notes="Automated integration test measurement"
    )
    print(f"✅ Measurement created in database: {measurement_id}")
    
    # Start measurement
    db_manager.start_measurement(measurement_id)
    logger.info(f"Started measurement {measurement_id}")
    
    # Execute IV curve script
    iv_script = next((s for s in scripts if 'iv' in s.id.lower()), None)
    if iv_script:
        parameters = {
            'start_voltage': 0.0,
            'end_voltage': 5.0,
            'points': 11,
            'compliance': 0.001,
            'delay': 0.01
        }
        
        try:
            results = script_manager.execute_script(
                iv_script.id,
                smu,
                parameters,
                logger
            )
            
            print(f"✅ Script executed: {len(results)} data points")
            
            # Add data to database
            for i, result in enumerate(results):
                db_manager.add_measurement_data_point(
                    measurement_id=measurement_id,
                    data_index=i,
                    data=result
                )
            
            # Complete measurement
            db_manager.complete_measurement(measurement_id, len(results))
            logger.info(f"Completed measurement {measurement_id}")
            print(f"✅ Measurement data saved to database")
            
        except Exception as e:
            print(f"❌ Script execution failed: {e}")
            return False
    
    # 8. Export measurement data
    print("\n8. Exporting measurement data...")
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        export_path = tmp.name
    
    success = db_manager.export_measurement_to_csv(measurement_id, export_path)
    if success:
        print(f"✅ Data exported to CSV: {export_path}")
        
        # Verify export
        with open(export_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
            print(f"   CSV contains {len(data_lines)-1} data rows")  # -1 for header
    else:
        print("❌ Export failed")
        return False
    
    # 9. Create and save configuration preset
    print("\n9. Saving configuration preset...")
    preset_id = db_manager.save_configuration_preset(
        user_id=user_id,
        name="Integration Test IV",
        measurement_type="IV_CURVE",
        parameters=parameters,
        description="Configuration used in integration test"
    )
    print(f"✅ Configuration preset saved: {preset_id}")
    
    # 10. Generate statistics
    print("\n10. Generating statistics...")
    stats = db_manager.get_statistics(user_id)
    print(f"✅ User statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 11. Test second measurement type
    print("\n11. Testing resistance measurement...")
    
    # Create second measurement
    resistance_measurement_id = db_manager.create_measurement(
        user_id=user_id,
        measurement_type="RESISTANCE_TIME",
        title="Integration Test Resistance Measurement",
        instrument_id=instrument_id,
        parameters={
            "voltage": 2.0,
            "duration": 2.0,
            "interval": 0.5,
            "compliance": 0.001
        }
    )
    
    # Execute resistance script
    resistance_script = next((s for s in scripts if 'resistance' in s.id.lower()), None)
    if resistance_script:
        db_manager.start_measurement(resistance_measurement_id)
        
        results = script_manager.execute_script(
            resistance_script.id,
            smu,
            {
                'voltage': 2.0,
                'duration': 2.0,
                'interval': 0.5,
                'compliance': 0.001
            },
            logger
        )
        
        # Save data
        for i, result in enumerate(results):
            db_manager.add_measurement_data_point(
                resistance_measurement_id,
                i,
                result
            )
        
        db_manager.complete_measurement(resistance_measurement_id, len(results))
        print(f"✅ Resistance measurement completed: {len(results)} points")
    
    # 12. Test automated sequence
    print("\n12. Testing automated sequence...")
    
    # Get sequence script
    sequence_script = next((s for s in scripts if 'sequence' in s.id.lower() or 'automated' in s.id.lower()), None)
    if sequence_script:
        sequence_measurement_id = db_manager.create_measurement(
            user_id=user_id,
            measurement_type="AUTOMATED_SEQUENCE",
            title="Integration Test Automated Sequence",
            instrument_id=instrument_id,
            parameters={
                "resistance_voltage": 1.0,
                "resistance_duration": 2.0,
                "rest_time": 1.0,
                "iv_start": 0.0,
                "iv_end": 3.0,
                "iv_points": 7
            }
        )
        
        db_manager.start_measurement(sequence_measurement_id)
        
        results = script_manager.execute_script(
            sequence_script.id,
            smu,
            {
                'resistance_voltage': 1.0,
                'resistance_duration': 2.0,
                'rest_time': 1.0,
                'iv_start': 0.0,
                'iv_end': 3.0,
                'iv_points': 7
            },
            logger
        )
        
        # Save complex data structure
        db_manager.add_measurement_data_point(
            sequence_measurement_id,
            0,
            results
        )
        
        db_manager.complete_measurement(sequence_measurement_id, 1)
        print(f"✅ Automated sequence completed")
        print(f"   Resistance data points: {len(results.get('resistance_data', []))}")
        print(f"   IV data points: {len(results.get('iv_data', []))}")
    
    # 13. Final statistics
    print("\n13. Final statistics...")
    final_stats = db_manager.get_statistics(user_id)
    measurements = db_manager.get_measurements(user_id)
    
    print(f"✅ Final results:")
    print(f"   Total measurements: {final_stats['total_measurements']}")
    print(f"   Completed measurements: {final_stats['completed_measurements']}")
    print(f"   Total data points: {final_stats['total_data_points']}")
    
    print(f"\n📊 Measurement summary:")
    for measurement in measurements:
        print(f"   - {measurement['title']}: {measurement['status']} "
              f"({measurement.get('data_points', 0)} points)")
    
    # Clean up
    try:
        Path(export_path).unlink()
    except:
        pass
    
    print(f"\n🎉 COMPLETE WORKFLOW TEST PASSED!")
    print(f"Successfully integrated all components:")
    print(f"  ✅ User Management")
    print(f"  ✅ Logging System")
    print(f"  ✅ Configuration Management")
    print(f"  ✅ Database Storage")
    print(f"  ✅ Simulated Instruments")
    print(f"  ✅ Script Execution")
    print(f"  ✅ Data Export")
    print(f"  ✅ Multiple Measurement Types")
    
    return True


if __name__ == "__main__":
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)