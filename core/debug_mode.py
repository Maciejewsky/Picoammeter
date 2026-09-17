"""
Debug mode and simulated instruments for Keithley LabNano3D
Provides simulated instruments for testing and development
"""

import random
import time
import math
from typing import Dict, List, Any, Optional
from datetime import datetime

class SimulatedInstrument:
    """Base class for simulated instruments"""
    
    def __init__(self, model: str, serial: str):
        self.model = model
        self.serial = serial
        self.connected = False
        self.output_enabled = False
        self.address = f"SIM::{model}::{serial}"
        self.last_command = None
        self.command_history = []
        
    def connect(self):
        """Simulate connection"""
        self.connected = True
        time.sleep(0.1)  # Simulate connection delay
    
    def disconnect(self):
        """Simulate disconnection"""
        self.connected = False
        self.output_enabled = False
    
    def write(self, command: str):
        """Simulate writing a command"""
        if not self.connected:
            raise Exception("Instrument not connected")
        
        self.last_command = command.strip()
        self.command_history.append({
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add random delay to simulate real instrument
        time.sleep(random.uniform(0.01, 0.05))
    
    def query(self, command: str) -> str:
        """Simulate querying a command"""
        self.write(command)
        return self._handle_query(command.strip())
    
    def _handle_query(self, command: str) -> str:
        """Handle query commands - to be overridden by subclasses"""
        if command == "*IDN?":
            return f"KEITHLEY INSTRUMENTS,{self.model},{self.serial},1.0.0"
        elif command == "*OPC?":
            return "1"
        else:
            return "0"

class SimulatedSMU2450(SimulatedInstrument):
    """Simulated SMU 2450 instrument"""
    
    def __init__(self, serial: str = "SIM001"):
        super().__init__("MODEL 2450", serial)
        self.voltage = 0.0
        self.current = 0.0
        self.voltage_limit = 200.0
        self.current_limit = 1.0
        self.resistance = 1000.0  # Default resistance for simulation
        
    def _handle_query(self, command: str) -> str:
        """Handle SMU 2450 specific commands"""
        base_response = super()._handle_query(command)
        if base_response != "0":
            return base_response
        
        command = command.upper()
        
        if command == "SOUR:VOLT?" or command == ":SOUR:VOLT?":
            return f"{self.voltage:.6f}"
        elif command == "SOUR:CURR?" or command == ":SOUR:CURR?":
            return f"{self.current:.9f}"
        elif command == "MEAS:VOLT?" or command == ":MEAS:VOLT?":
            # Add some noise to simulation
            noise = random.uniform(-0.001, 0.001)
            return f"{self.voltage + noise:.6f}"
        elif command == "MEAS:CURR?" or command == ":MEAS:CURR?":
            # Simulate current based on voltage and resistance
            if self.output_enabled:
                calculated_current = self.voltage / self.resistance
                noise = random.uniform(-1e-9, 1e-9)
                return f"{calculated_current + noise:.9f}"
            else:
                return "0.000000000"
        elif command == "MEAS:RES?" or command == ":MEAS:RES?":
            # Simulate resistance measurement with some variation
            variation = random.uniform(0.95, 1.05)
            return f"{self.resistance * variation:.3f}"
        elif command == "OUTP?" or command == ":OUTP?":
            return "1" if self.output_enabled else "0"
        else:
            return "0"
    
    def write(self, command: str):
        """Handle SMU 2450 specific write commands"""
        super().write(command)
        
        command = command.strip().upper()
        
        if command.startswith("SOUR:VOLT ") or command.startswith(":SOUR:VOLT "):
            try:
                voltage_str = command.split()[-1]
                self.voltage = float(voltage_str)
            except ValueError:
                pass
        elif command.startswith("SOUR:CURR ") or command.startswith(":SOUR:CURR "):
            try:
                current_str = command.split()[-1]
                self.current = float(current_str)
            except ValueError:
                pass
        elif command == "OUTP ON" or command == ":OUTP ON":
            self.output_enabled = True
        elif command == "OUTP OFF" or command == ":OUTP OFF":
            self.output_enabled = False
        elif command.startswith("SOUR:VOLT:LIM "):
            try:
                limit_str = command.split()[-1]
                self.voltage_limit = float(limit_str)
            except ValueError:
                pass

class SimulatedPico6487(SimulatedInstrument):
    """Simulated Picoammeter 6487 instrument"""
    
    def __init__(self, serial: str = "SIM002"):
        super().__init__("MODEL 6487", serial)
        self.voltage = 0.0
        self.current_range = 2e-9  # 2nA range
        self.auto_range = True
        
    def _handle_query(self, command: str) -> str:
        """Handle Picoammeter 6487 specific commands"""
        base_response = super()._handle_query(command)
        if base_response != "0":
            return base_response
        
        command = command.upper()
        
        if command == "SOUR:VOLT?" or command == ":SOUR:VOLT?":
            return f"{self.voltage:.6f}"
        elif command == "MEAS:CURR?" or command == ":MEAS:CURR?":
            # Simulate very low current measurement
            base_current = random.uniform(-1e-12, 1e-12)  # Picoampere range
            if self.voltage != 0:
                # Add some voltage-dependent current
                voltage_current = self.voltage * random.uniform(1e-15, 1e-13)
                base_current += voltage_current
            return f"{base_current:.15f}"
        elif command == "CURR:RANG?" or command == ":CURR:RANG?":
            return f"{self.current_range:.12f}"
        elif command == "CURR:RANG:AUTO?" or command == ":CURR:RANG:AUTO?":
            return "1" if self.auto_range else "0"
        else:
            return "0"
    
    def write(self, command: str):
        """Handle Picoammeter 6487 specific write commands"""
        super().write(command)
        
        command = command.strip().upper()
        
        if command.startswith("SOUR:VOLT ") or command.startswith(":SOUR:VOLT "):
            try:
                voltage_str = command.split()[-1]
                self.voltage = float(voltage_str)
            except ValueError:
                pass
        elif command.startswith("CURR:RANG "):
            try:
                range_str = command.split()[-1]
                self.current_range = float(range_str)
                self.auto_range = False
            except ValueError:
                pass
        elif command == "CURR:RANG:AUTO ON" or command == ":CURR:RANG:AUTO ON":
            self.auto_range = True
        elif command == "CURR:RANG:AUTO OFF" or command == ":CURR:RANG:AUTO OFF":
            self.auto_range = False

class DebugInstrumentManager:
    """Manages simulated instruments for debug mode"""
    
    def __init__(self):
        self.instruments = {}
        self.create_default_instruments()
    
    def create_default_instruments(self):
        """Create default simulated instruments"""
        # Create SMU 2450 instruments
        for i in range(2):
            serial = f"SIM{2450}{i:03d}"
            smu = SimulatedSMU2450(serial)
            self.instruments[f"SMU_2450_{i+1}"] = smu
        
        # Create Picoammeter 6487 instruments
        for i in range(2):
            serial = f"SIM{6487}{i:03d}"
            pico = SimulatedPico6487(serial)
            self.instruments[f"PICO_6487_{i+1}"] = pico
    
    def list_available_instruments(self) -> List[Dict[str, str]]:
        """List available simulated instruments"""
        instruments = []
        for name, instrument in self.instruments.items():
            instruments.append({
                "name": name,
                "model": instrument.model,
                "serial": instrument.serial,
                "address": instrument.address,
                "connected": instrument.connected
            })
        return instruments
    
    def get_instrument(self, name: str) -> Optional[SimulatedInstrument]:
        """Get simulated instrument by name"""
        return self.instruments.get(name)
    
    def connect_instrument(self, name: str) -> bool:
        """Connect to simulated instrument"""
        instrument = self.instruments.get(name)
        if instrument:
            instrument.connect()
            return True
        return False
    
    def disconnect_instrument(self, name: str) -> bool:
        """Disconnect from simulated instrument"""
        instrument = self.instruments.get(name)
        if instrument:
            instrument.disconnect()
            return True
        return False
    
    def add_custom_instrument(self, name: str, model_type: str, serial: str = None):
        """Add custom simulated instrument"""
        if serial is None:
            serial = f"CUSTOM{len(self.instruments):03d}"
        
        if model_type.upper() == "SMU2450":
            instrument = SimulatedSMU2450(serial)
        elif model_type.upper() == "PICO6487":
            instrument = SimulatedPico6487(serial)
        else:
            raise ValueError(f"Unsupported instrument type: {model_type}")
        
        self.instruments[name] = instrument
        return instrument

# Global debug manager instance
_debug_manager = None

def get_debug_manager() -> DebugInstrumentManager:
    """Get the global debug instrument manager"""
    global _debug_manager
    if _debug_manager is None:
        _debug_manager = DebugInstrumentManager()
    return _debug_manager

def is_debug_mode_available() -> bool:
    """Check if debug mode is available"""
    return True  # Always available for testing