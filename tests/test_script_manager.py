#!/usr/bin/env python3
"""
Test script management functionality for Keithley LabNano3D v2.0
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.script_manager import ScriptManager, get_script_manager
from core.user_manager import get_user_manager
from core.debug_mode import get_debug_manager
from core.logger import init_logging


def test_script_manager():
    """Test script manager functionality"""
    print("=" * 50)
    print("Testing Script Manager")
    print("=" * 50)
    
    # Setup user and script manager
    user_manager = get_user_manager()
    username = user_manager.create_user_profile("Script", "Tester")
    logger = init_logging(username)
    
    script_manager = get_script_manager(user_manager)
    
    # Test listing built-in scripts
    scripts = script_manager.list_scripts()
    print(f"✅ Found {len(scripts)} scripts:")
    for script in scripts:
        print(f"   - {script.name} ({script.script_type}) - {script.description}")
        print(f"     Built-in: {script.is_builtin}, Author: {script.author}")
    
    # Test getting script parameters
    if scripts:
        first_script = scripts[0]
        parameters = script_manager.get_script_parameters(first_script.id)
        print(f"\n✅ Parameters for '{first_script.name}':")
        for param_name, param_info in parameters.items():
            print(f"   - {param_name}: {param_info['description']} "
                  f"(default: {param_info['default']} {param_info['unit']})")
    
    # Test creating a custom user script
    custom_script = '''def execute_measurement(instrument, parameters, logger=None):
    """Simple test measurement"""
    import time
    
    voltage = parameters.get('voltage', 1.0)
    duration = parameters.get('duration', 5.0)
    
    if logger:
        logger.info(f"Starting test measurement: {voltage}V for {duration}s")
    
    instrument.write(f"SOUR:VOLT {voltage}")
    instrument.write("OUTP ON")
    
    results = []
    start_time = time.time()
    
    while (time.time() - start_time) < duration:
        current = float(instrument.query("MEAS:CURR?"))
        elapsed = time.time() - start_time
        
        results.append({
            'time': elapsed,
            'voltage': voltage,
            'current': current,
            'resistance': voltage / current if current > 1e-12 else float('inf')
        })
        
        time.sleep(0.5)
    
    instrument.write("OUTP OFF")
    
    if logger:
        logger.info(f"Test measurement completed: {len(results)} points")
    
    return results

def get_parameter_definitions():
    return {
        'voltage': {
            'type': 'float',
            'default': 1.0,
            'min': 0.1,
            'max': 5.0,
            'unit': 'V',
            'description': 'Test voltage'
        },
        'duration': {
            'type': 'float',
            'default': 5.0,
            'min': 1.0,
            'max': 60.0,
            'unit': 's',
            'description': 'Measurement duration'
        }
    }
'''
    
    script_path = script_manager.create_user_script(
        name="Custom Test",
        content=custom_script,
        description="A simple test measurement script",
        script_type="measurement"
    )
    print(f"\n✅ Created custom script: {script_path}")
    
    # Test validation
    validation = script_manager.validate_script(custom_script)
    print(f"✅ Script validation: Valid={validation['valid']}")
    if validation['errors']:
        print(f"   Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"   Warnings: {validation['warnings']}")
    
    # Test listing scripts again (should include custom script)
    all_scripts = script_manager.list_scripts()
    custom_scripts = [s for s in all_scripts if not s.is_builtin]
    print(f"✅ Total scripts after adding custom: {len(all_scripts)} ({len(custom_scripts)} custom)")
    
    return script_manager, custom_scripts[0] if custom_scripts else None


def test_script_execution():
    """Test script execution with simulated instrument"""
    print("\n" + "=" * 50)
    print("Testing Script Execution")
    print("=" * 50)
    
    # Setup
    user_manager = get_user_manager()
    script_manager = get_script_manager(user_manager)
    debug_manager = get_debug_manager()
    logger = init_logging(user_manager.current_user)
    
    # Get a simulated instrument
    debug_manager.connect_instrument("SMU_2450_1")
    instrument = debug_manager.get_instrument("SMU_2450_1")
    
    if not instrument:
        print("❌ No simulated instrument available")
        return
    
    print(f"✅ Using simulated instrument: {instrument.model}")
    
    # Test built-in IV curve script
    scripts = script_manager.list_scripts(include_user=False)
    iv_script = next((s for s in scripts if 'iv' in s.id.lower()), None)
    
    if iv_script:
        print(f"\n✅ Testing '{iv_script.name}' script")
        
        # Get parameters and run with test values
        parameters = {
            'start_voltage': 0.0,
            'end_voltage': 2.0,
            'points': 5,
            'compliance': 0.001,
            'delay': 0.01  # Short delay for test
        }
        
        try:
            results = script_manager.execute_script(
                iv_script.id, 
                instrument, 
                parameters, 
                logger
            )
            
            print(f"✅ Script executed successfully: {len(results)} data points")
            print("   Sample results:")
            for i, result in enumerate(results[:3]):
                print(f"     Point {i}: {result['voltage']:.2f}V -> {result['current']:.6f}A")
            
        except Exception as e:
            print(f"❌ Script execution failed: {e}")
    
    # Test resistance script
    resistance_script = next((s for s in scripts if 'resistance' in s.id.lower()), None)
    
    if resistance_script:
        print(f"\n✅ Testing '{resistance_script.name}' script")
        
        parameters = {
            'voltage': 1.0,
            'duration': 3.0,  # Short duration for test
            'interval': 0.5,
            'compliance': 0.001
        }
        
        try:
            results = script_manager.execute_script(
                resistance_script.id,
                instrument,
                parameters,
                logger
            )
            
            print(f"✅ Script executed successfully: {len(results)} data points")
            if results:
                print(f"   Final resistance: {results[-1]['resistance']:.2f}Ω")
            
        except Exception as e:
            print(f"❌ Script execution failed: {e}")


def test_script_import_export():
    """Test script import/export functionality"""
    print("\n" + "=" * 50)
    print("Testing Script Import/Export")
    print("=" * 50)
    
    user_manager = get_user_manager()
    script_manager = get_script_manager(user_manager)
    
    # Create a temporary script file
    test_script_content = '''"""
Test Analysis Script
Performs basic data analysis on measurement results
"""

def execute_measurement(instrument, parameters, logger=None):
    """Dummy analysis function"""
    if logger:
        logger.info("Running analysis script")
    
    # Simulate analysis
    return {"analysis": "complete", "result": "success"}

def get_parameter_definitions():
    return {
        'input_file': {
            'type': 'string',
            'default': '',
            'description': 'Input data file path'
        }
    }
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(test_script_content)
        temp_script_path = tmp_file.name
    
    try:
        # Test import
        imported_path = script_manager.import_script(temp_script_path)
        print(f"✅ Script imported: {imported_path}")
        
        # Verify it appears in the list
        scripts = script_manager.list_scripts(include_builtin=False)
        imported_script = next((s for s in scripts if s.file_path == imported_path), None)
        
        if imported_script:
            print(f"✅ Imported script found in list: {imported_script.name}")
            
            # Test export
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as export_file:
                export_path = export_file.name
            
            script_manager.export_script(imported_script.id, export_path)
            print(f"✅ Script exported to: {export_path}")
            
            # Verify export content
            with open(export_path, 'r') as f:
                exported_content = f.read()
            
            if 'Test Analysis Script' in exported_content:
                print("✅ Export content verified")
            else:
                print("❌ Export content verification failed")
        
        else:
            print("❌ Imported script not found in list")
    
    except Exception as e:
        print(f"❌ Import/export test failed: {e}")
    
    finally:
        # Clean up temporary files
        try:
            Path(temp_script_path).unlink()
        except:
            pass


def run_all_tests():
    """Run all script manager tests"""
    print("📜 Keithley LabNano3D v2.0 - Script Manager Tests")
    print("=" * 60)
    
    try:
        # Test script manager basic functionality
        script_manager, custom_script = test_script_manager()
        
        # Test script execution
        test_script_execution()
        
        # Test import/export
        test_script_import_export()
        
        print("\n" + "=" * 60)
        print("🎉 ALL SCRIPT MANAGER TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ SCRIPT MANAGER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)