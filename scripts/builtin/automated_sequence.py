# Automated Measurement Sequence Script
# This script performs a sequence of resistance and IV measurements

def execute_measurement(instrument, parameters, logger=None):
    """
    Execute automated measurement sequence
    
    Parameters:
    - resistance_voltage: Voltage for resistance measurement (V)
    - resistance_duration: Duration for resistance measurement (s)
    - rest_time: Time between measurements (s)
    - iv_start: Start voltage for IV curve (V)
    - iv_end: End voltage for IV curve (V)
    - iv_points: Number of IV points
    """
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
    """Return parameter definitions for the script"""
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
