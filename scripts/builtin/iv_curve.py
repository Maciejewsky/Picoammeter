# IV Curve Measurement Script
# This script performs a voltage sweep and measures current

def execute_measurement(instrument, parameters, logger=None):
    """
    Execute IV curve measurement
    
    Parameters:
    - start_voltage: Starting voltage (V)
    - end_voltage: Ending voltage (V)
    - points: Number of measurement points
    - compliance: Current compliance (A)
    - delay: Delay between points (s)
    """
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
    """Return parameter definitions for the script"""
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
