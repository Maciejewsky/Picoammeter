# Resistance vs Time Measurement Script
# This script measures resistance over time at a fixed voltage

def execute_measurement(instrument, parameters, logger=None):
    """
    Execute resistance vs time measurement
    
    Parameters:
    - voltage: Test voltage (V)
    - duration: Measurement duration (s)
    - interval: Time between measurements (s)
    - compliance: Current compliance (A)
    """
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
    """Return parameter definitions for the script"""
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
