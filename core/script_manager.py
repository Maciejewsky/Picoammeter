"""
Script management system for Keithley LabNano3D
Allows users to create, edit, load, and execute custom measurement scripts
"""

import os
import json
import importlib.util
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class Script:
    """Data class for script information"""
    id: str
    name: str
    description: str
    script_type: str  # 'measurement', 'analysis', 'automation'
    file_path: str
    parameters: Dict[str, Any]
    author: str
    created_at: str
    modified_at: str
    version: str
    tags: List[str]
    is_builtin: bool = False


class ScriptManager:
    """Manages custom scripts for measurements and automation"""
    
    def __init__(self, user_manager=None):
        self.user_manager = user_manager
        self.builtin_scripts_dir = Path("scripts") / "builtin"
        self.user_scripts_dir = None
        
        if user_manager and user_manager.current_user:
            self.user_scripts_dir = user_manager.get_user_directory("scripts")
        
        # Create directories
        self.builtin_scripts_dir.mkdir(parents=True, exist_ok=True)
        if self.user_scripts_dir:
            self.user_scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create builtin scripts
        self.create_builtin_scripts()
    
    def create_builtin_scripts(self):
        """Create built-in example scripts"""
        
        # IV Curve measurement script
        iv_script = """# IV Curve Measurement Script
# This script performs a voltage sweep and measures current

def execute_measurement(instrument, parameters, logger=None):
    \"\"\"
    Execute IV curve measurement
    
    Parameters:
    - start_voltage: Starting voltage (V)
    - end_voltage: Ending voltage (V)
    - points: Number of measurement points
    - compliance: Current compliance (A)
    - delay: Delay between points (s)
    \"\"\"
    import time
    
    # Get parameters with defaults
    start_v = parameters.get('start_voltage', 0.0)
    end_v = parameters.get('end_voltage', 1.0)
    points = parameters.get('points', 11)
    compliance = parameters.get('compliance', 0.001)
    delay = parameters.get('delay', 0.1)
    
    if logger:
        logger.info(f"Starting IV curve: {start_v}V to {end_v}V, {points} points")
    
    # Setup instrument
    instrument.write(f"SOUR:CURR:COMP {compliance}")
    instrument.write("SOUR:FUNC VOLT")
    instrument.write("SENS:FUNC 'CURR'")
    instrument.write("OUTP ON")
    
    # Calculate voltage step
    if points > 1:
        step = (end_v - start_v) / (points - 1)
    else:
        step = 0
    
    results = []
    
    try:
        for i in range(points):
            voltage = start_v + i * step
            
            # Set voltage
            instrument.write(f"SOUR:VOLT {voltage}")
            time.sleep(delay)
            
            # Measure current
            current = float(instrument.query("MEAS:CURR?"))
            
            # Calculate resistance and power
            resistance = voltage / current if abs(current) > 1e-12 else float('inf')
            power = voltage * current
            
            result = {
                'point': i,
                'voltage': voltage,
                'current': current,
                'resistance': resistance,
                'power': power,
                'timestamp': time.time()
            }
            
            results.append(result)
            
            if logger:
                logger.debug(f"Point {i}: {voltage}V -> {current}A")
    
    finally:
        # Turn off output
        instrument.write("OUTP OFF")
        if logger:
            logger.info("IV curve measurement completed")
    
    return results


def get_parameter_definitions():
    \"\"\"Return parameter definitions for the script\"\"\"
    return {
        'start_voltage': {
            'type': 'float',
            'default': 0.0,
            'min': -10.0,
            'max': 10.0,
            'unit': 'V',
            'description': 'Starting voltage for sweep'
        },
        'end_voltage': {
            'type': 'float',
            'default': 1.0,
            'min': -10.0,
            'max': 10.0,
            'unit': 'V',
            'description': 'Ending voltage for sweep'
        },
        'points': {
            'type': 'int',
            'default': 11,
            'min': 2,
            'max': 1000,
            'unit': '',
            'description': 'Number of measurement points'
        },
        'compliance': {
            'type': 'float',
            'default': 0.001,
            'min': 1e-9,
            'max': 1.0,
            'unit': 'A',
            'description': 'Current compliance limit'
        },
        'delay': {
            'type': 'float',
            'default': 0.1,
            'min': 0.001,
            'max': 10.0,
            'unit': 's',
            'description': 'Delay between measurements'
        }
    }
"""
        
        iv_script_path = self.builtin_scripts_dir / "iv_curve.py"
        if not iv_script_path.exists():
            with open(iv_script_path, 'w') as f:
                f.write(iv_script)
        
        # Resistance vs Time script
        resistance_script = """# Resistance vs Time Measurement Script
# This script measures resistance over time at a fixed voltage

def execute_measurement(instrument, parameters, logger=None):
    \"\"\"
    Execute resistance vs time measurement
    
    Parameters:
    - voltage: Test voltage (V)
    - duration: Measurement duration (s)
    - interval: Time between measurements (s)
    - compliance: Current compliance (A)
    \"\"\"
    import time
    
    # Get parameters with defaults
    voltage = parameters.get('voltage', 1.0)
    duration = parameters.get('duration', 60.0)
    interval = parameters.get('interval', 1.0)
    compliance = parameters.get('compliance', 0.001)
    
    if logger:
        logger.info(f"Starting resistance measurement: {voltage}V for {duration}s")
    
    # Setup instrument
    instrument.write(f"SOUR:VOLT {voltage}")
    instrument.write(f"SOUR:CURR:COMP {compliance}")
    instrument.write("SOUR:FUNC VOLT")
    instrument.write("SENS:FUNC 'CURR'")
    instrument.write("OUTP ON")
    
    results = []
    start_time = time.time()
    point = 0
    
    try:
        while (time.time() - start_time) < duration:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Measure current
            current = float(instrument.query("MEAS:CURR?"))
            
            # Calculate resistance
            resistance = voltage / current if abs(current) > 1e-12 else float('inf')
            
            result = {
                'point': point,
                'time': elapsed,
                'voltage': voltage,
                'current': current,
                'resistance': resistance,
                'timestamp': current_time
            }
            
            results.append(result)
            
            if logger and point % 10 == 0:  # Log every 10th point
                logger.debug(f"t={elapsed:.1f}s: R={resistance:.2f}Ω")
            
            point += 1
            
            # Wait for next measurement
            time.sleep(interval)
    
    finally:
        # Turn off output
        instrument.write("OUTP OFF")
        if logger:
            logger.info(f"Resistance measurement completed: {point} points")
    
    return results


def get_parameter_definitions():
    \"\"\"Return parameter definitions for the script\"\"\"
    return {
        'voltage': {
            'type': 'float',
            'default': 1.0,
            'min': 0.1,
            'max': 10.0,
            'unit': 'V',
            'description': 'Test voltage'
        },
        'duration': {
            'type': 'float',
            'default': 60.0,
            'min': 1.0,
            'max': 3600.0,
            'unit': 's',
            'description': 'Measurement duration'
        },
        'interval': {
            'type': 'float',
            'default': 1.0,
            'min': 0.1,
            'max': 60.0,
            'unit': 's',
            'description': 'Time between measurements'
        },
        'compliance': {
            'type': 'float',
            'default': 0.001,
            'min': 1e-9,
            'max': 1.0,
            'unit': 'A',
            'description': 'Current compliance limit'
        }
    }
"""
        
        resistance_script_path = self.builtin_scripts_dir / "resistance_time.py"
        if not resistance_script_path.exists():
            with open(resistance_script_path, 'w') as f:
                f.write(resistance_script)
        
        # Automated sequence script
        sequence_script = """# Automated Measurement Sequence Script
# This script performs a sequence of resistance and IV measurements

def execute_measurement(instrument, parameters, logger=None):
    \"\"\"
    Execute automated measurement sequence
    
    Parameters:
    - resistance_voltage: Voltage for resistance measurement (V)
    - resistance_duration: Duration for resistance measurement (s)
    - rest_time: Time between measurements (s)
    - iv_start: Start voltage for IV curve (V)
    - iv_end: End voltage for IV curve (V)
    - iv_points: Number of IV points
    \"\"\"
    import time
    
    # Get parameters
    r_voltage = parameters.get('resistance_voltage', 1.0)
    r_duration = parameters.get('resistance_duration', 30.0)
    rest_time = parameters.get('rest_time', 5.0)
    iv_start = parameters.get('iv_start', 0.0)
    iv_end = parameters.get('iv_end', 2.0)
    iv_points = parameters.get('iv_points', 21)
    
    if logger:
        logger.info("Starting automated sequence measurement")
    
    results = {
        'resistance_data': [],
        'iv_data': [],
        'sequence_info': {
            'resistance_phase_duration': r_duration,
            'rest_time': rest_time,
            'iv_points': iv_points
        }
    }
    
    # Phase 1: Resistance measurement
    if logger:
        logger.info(f"Phase 1: Resistance measurement ({r_duration}s)")
    
    instrument.write(f"SOUR:VOLT {r_voltage}")
    instrument.write("SOUR:CURR:COMP 0.001")
    instrument.write("OUTP ON")
    
    start_time = time.time()
    point = 0
    
    while (time.time() - start_time) < r_duration:
        current = float(instrument.query("MEAS:CURR?"))
        resistance = r_voltage / current if abs(current) > 1e-12 else float('inf')
        
        results['resistance_data'].append({
            'point': point,
            'time': time.time() - start_time,
            'voltage': r_voltage,
            'current': current,
            'resistance': resistance
        })
        
        point += 1
        time.sleep(1.0)
    
    # Turn off and rest
    instrument.write("OUTP OFF")
    if logger:
        logger.info(f"Resting for {rest_time}s")
    time.sleep(rest_time)
    
    # Phase 2: IV curve
    if logger:
        logger.info(f"Phase 2: IV curve ({iv_start}V to {iv_end}V)")
    
    instrument.write("OUTP ON")
    step = (iv_end - iv_start) / (iv_points - 1) if iv_points > 1 else 0
    
    for i in range(iv_points):
        voltage = iv_start + i * step
        instrument.write(f"SOUR:VOLT {voltage}")
        time.sleep(0.1)
        
        current = float(instrument.query("MEAS:CURR?"))
        resistance = voltage / current if abs(current) > 1e-12 else float('inf')
        
        results['iv_data'].append({
            'point': i,
            'voltage': voltage,
            'current': current,
            'resistance': resistance,
            'power': voltage * current
        })
    
    instrument.write("OUTP OFF")
    
    if logger:
        logger.info("Automated sequence completed")
    
    return results


def get_parameter_definitions():
    \"\"\"Return parameter definitions for the script\"\"\"
    return {
        'resistance_voltage': {
            'type': 'float',
            'default': 1.0,
            'min': 0.1,
            'max': 5.0,
            'unit': 'V',
            'description': 'Voltage for resistance measurement'
        },
        'resistance_duration': {
            'type': 'float',
            'default': 30.0,
            'min': 5.0,
            'max': 300.0,
            'unit': 's',
            'description': 'Duration of resistance measurement'
        },
        'rest_time': {
            'type': 'float',
            'default': 5.0,
            'min': 0.0,
            'max': 60.0,
            'unit': 's',
            'description': 'Rest time between measurements'
        },
        'iv_start': {
            'type': 'float',
            'default': 0.0,
            'min': -5.0,
            'max': 5.0,
            'unit': 'V',
            'description': 'Start voltage for IV curve'
        },
        'iv_end': {
            'type': 'float',
            'default': 2.0,
            'min': -5.0,
            'max': 5.0,
            'unit': 'V',
            'description': 'End voltage for IV curve'
        },
        'iv_points': {
            'type': 'int',
            'default': 21,
            'min': 5,
            'max': 100,
            'unit': '',
            'description': 'Number of IV curve points'
        }
    }
"""
        
        sequence_script_path = self.builtin_scripts_dir / "automated_sequence.py"
        if not sequence_script_path.exists():
            with open(sequence_script_path, 'w') as f:
                f.write(sequence_script)
    
    def list_scripts(self, include_builtin=True, include_user=True) -> List[Script]:
        """List available scripts"""
        scripts = []
        
        # Built-in scripts
        if include_builtin and self.builtin_scripts_dir.exists():
            for script_file in self.builtin_scripts_dir.glob("*.py"):
                script_info = self._get_script_info(script_file, is_builtin=True)
                if script_info:
                    scripts.append(script_info)
        
        # User scripts
        if include_user and self.user_scripts_dir and self.user_scripts_dir.exists():
            for script_file in self.user_scripts_dir.glob("*.py"):
                script_info = self._get_script_info(script_file, is_builtin=False)
                if script_info:
                    scripts.append(script_info)
        
        return scripts
    
    def _get_script_info(self, script_path: Path, is_builtin: bool) -> Optional[Script]:
        """Extract script information from file"""
        try:
            # Read the script file
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Get file stats
            stat = script_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Extract basic info from filename and content
            name = script_path.stem.replace('_', ' ').title()
            
            # Try to extract description from docstring
            description = "Custom measurement script"
            if '"""' in content:
                start = content.find('"""')
                if start != -1:
                    start += 3
                    end = content.find('"""', start)
                    if end != -1:
                        docstring = content[start:end].strip()
                        if docstring:
                            description = docstring.split('\n')[0]
            
            # Determine script type
            script_type = "measurement"
            if "analysis" in script_path.name.lower():
                script_type = "analysis"
            elif "automation" in script_path.name.lower() or "sequence" in script_path.name.lower():
                script_type = "automation"
            
            return Script(
                id=script_path.stem,
                name=name,
                description=description,
                script_type=script_type,
                file_path=str(script_path),
                parameters={},
                author="System" if is_builtin else (self.user_manager.current_user if self.user_manager else "User"),
                created_at=created_at,
                modified_at=modified_at,
                version="1.0",
                tags=[script_type],
                is_builtin=is_builtin
            )
        
        except Exception as e:
            print(f"Error reading script {script_path}: {e}")
            return None
    
    def load_script(self, script_id: str):
        """Load and return a script module"""
        scripts = self.list_scripts()
        script = next((s for s in scripts if s.id == script_id), None)
        
        if not script:
            raise ValueError(f"Script '{script_id}' not found")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(script_id, script.file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def execute_script(self, script_id: str, instrument, parameters: Dict[str, Any], logger=None):
        """Execute a script with given parameters"""
        module = self.load_script(script_id)
        
        if not hasattr(module, 'execute_measurement'):
            raise ValueError(f"Script '{script_id}' does not have an execute_measurement function")
        
        return module.execute_measurement(instrument, parameters, logger)
    
    def get_script_parameters(self, script_id: str) -> Dict[str, Any]:
        """Get parameter definitions for a script"""
        module = self.load_script(script_id)
        
        if hasattr(module, 'get_parameter_definitions'):
            return module.get_parameter_definitions()
        
        return {}
    
    def create_user_script(self, name: str, content: str, description: str = "", script_type: str = "measurement") -> str:
        """Create a new user script"""
        if not self.user_scripts_dir:
            raise ValueError("No user logged in")
        
        # Sanitize filename
        filename = name.lower().replace(' ', '_').replace('-', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '_')
        script_path = self.user_scripts_dir / f"{filename}.py"
        
        # Add metadata comment to content
        header = f'''"""
{name}
{description}

Created: {datetime.now().isoformat()}
Author: {self.user_manager.current_user if self.user_manager else "User"}
Type: {script_type}
"""

'''
        
        full_content = header + content
        
        # Write the script
        with open(script_path, 'w') as f:
            f.write(full_content)
        
        return str(script_path)
    
    def edit_user_script(self, script_id: str, content: str):
        """Edit an existing user script"""
        scripts = self.list_scripts(include_builtin=False)
        script = next((s for s in scripts if s.id == script_id), None)
        
        if not script:
            raise ValueError(f"User script '{script_id}' not found")
        
        if script.is_builtin:
            raise ValueError("Cannot edit built-in scripts")
        
        # Update modification time in content
        if '"""' in content:
            # Update metadata if present
            pass  # Could implement metadata update here
        
        with open(script.file_path, 'w') as f:
            f.write(content)
    
    def delete_user_script(self, script_id: str):
        """Delete a user script"""
        scripts = self.list_scripts(include_builtin=False)
        script = next((s for s in scripts if s.id == script_id), None)
        
        if not script:
            raise ValueError(f"User script '{script_id}' not found")
        
        if script.is_builtin:
            raise ValueError("Cannot delete built-in scripts")
        
        os.remove(script.file_path)
    
    def import_script(self, file_path: str) -> str:
        """Import a script from external file"""
        if not self.user_scripts_dir:
            raise ValueError("No user logged in")
        
        source_path = Path(file_path)
        if not source_path.exists():
            raise ValueError(f"Script file not found: {file_path}")
        
        # Read source script
        with open(source_path, 'r') as f:
            content = f.read()
        
        # Copy to user scripts directory
        dest_path = self.user_scripts_dir / source_path.name
        with open(dest_path, 'w') as f:
            f.write(content)
        
        return str(dest_path)
    
    def export_script(self, script_id: str, dest_path: str):
        """Export a script to external file"""
        scripts = self.list_scripts()
        script = next((s for s in scripts if s.id == script_id), None)
        
        if not script:
            raise ValueError(f"Script '{script_id}' not found")
        
        # Read source script
        with open(script.file_path, 'r') as f:
            content = f.read()
        
        # Write to destination
        with open(dest_path, 'w') as f:
            f.write(content)
    
    def validate_script(self, script_content: str) -> Dict[str, Any]:
        """Validate script syntax and required functions"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'has_execute_function': False,
            'has_parameter_function': False
        }
        
        try:
            # Check syntax by compiling
            compile(script_content, '<script>', 'exec')
        except SyntaxError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Syntax error: {e}")
            return validation_result
        
        # Check for required functions
        if 'def execute_measurement(' in script_content:
            validation_result['has_execute_function'] = True
        else:
            validation_result['warnings'].append("Script should have an 'execute_measurement' function")
        
        if 'def get_parameter_definitions(' in script_content:
            validation_result['has_parameter_function'] = True
        else:
            validation_result['warnings'].append("Script should have a 'get_parameter_definitions' function")
        
        # Check for common issues
        if 'instrument.write(' not in script_content and 'instrument.query(' not in script_content:
            validation_result['warnings'].append("Script doesn't seem to interact with instrument")
        
        return validation_result


# Global script manager instance
_script_manager = None

def get_script_manager(user_manager=None) -> ScriptManager:
    """Get the global script manager instance"""
    global _script_manager
    if _script_manager is None or (user_manager and _script_manager.user_manager != user_manager):
        _script_manager = ScriptManager(user_manager)
    return _script_manager