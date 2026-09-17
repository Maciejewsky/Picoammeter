"""
ESP32 Manager for Keithley LabNano3D
Handles communication with ESP32 devices via serial/USB
Supports ADS1115 ADC readings
"""

import serial
import serial.tools.list_ports
import time
import json
from typing import List, Dict, Optional, Tuple
from core.logger import get_logger


class ADS1115Channel:
    """Represents an ADS1115 channel configuration"""
    
    # Single-ended channels
    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3
    
    # Differential channels
    A0_A1 = 4
    A0_A3 = 5
    A2_A3 = 6
    A1_A3 = 7


class ADS1115Gain:
    """ADS1115 programmable gain amplifier settings"""
    
    GAIN_TWOTHIRDS = 0  # +/- 6.144V
    GAIN_ONE = 1        # +/- 4.096V
    GAIN_TWO = 2        # +/- 2.048V
    GAIN_FOUR = 3       # +/- 1.024V
    GAIN_EIGHT = 4      # +/- 0.512V
    GAIN_SIXTEEN = 5    # +/- 0.256V


class ADS1115Calibration:
    """Calibration settings for ADS1115 channel"""
    
    def __init__(self, channel: int = ADS1115Channel.A0):
        self.channel = channel
        self.raw_min = 0
        self.raw_max = 32767  # Maximum positive value for signed 16-bit integer (ADS1115 is 16-bit)
        self.inverted = False
        self.reading_type = "raw"  # "raw" or "percentage"
        self.label = "ADS1115"
        self.unit = "bits"
    
    def calibrate(self, min_value: float, max_value: float):
        """Set calibration min/max values"""
        self.raw_min = min_value
        self.raw_max = max_value
        
        # Detect if inverted
        if self.raw_min > self.raw_max:
            self.inverted = True
            self.raw_min, self.raw_max = self.raw_max, self.raw_min
    
    def set_reading_type(self, reading_type: str, label: str = None, unit: str = None):
        """Set the reading type: 'raw' or 'percentage'"""
        self.reading_type = reading_type
        if label:
            self.label = label
        if unit:
            self.unit = unit
    
    def convert_reading(self, raw_value: float) -> float:
        """Convert raw ADC value according to calibration"""
        if self.reading_type == "raw":
            return raw_value
        
        elif self.reading_type == "percentage":
            # Convert to 0-100% scale
            if self.raw_max == self.raw_min:
                return 0.0
            
            normalized = (raw_value - self.raw_min) / (self.raw_max - self.raw_min)
            
            if self.inverted:
                normalized = 1.0 - normalized
            
            return max(0.0, min(100.0, normalized * 100.0))
        
        return raw_value


class ESP32Device:
    """Represents a connected ESP32 device"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.connected = False
        self.logger = get_logger()
        
        # Device info
        self.device_id = None
        self.firmware_version = None
        
        # ADS1115 calibration
        self.calibration = ADS1115Calibration()
    
    def connect(self) -> bool:
        """Connect to ESP32 device"""
        try:
            self.logger.info(f"Attempting to connect to ESP32 on {self.port} at {self.baudrate} baud")
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for connection to stabilize
            self.logger.debug("Waiting for connection to stabilize...")
            time.sleep(0.5)
            
            # Clear any pending data
            self.logger.debug("Clearing serial buffers...")
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Wait a bit more for ESP32 to be ready
            time.sleep(0.3)
            
            # Check if there's any data in the buffer (startup messages)
            if self.serial.in_waiting > 0:
                startup_msg = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                self.logger.info(f"ESP32 startup messages:\n{startup_msg}")
            
            # Try to get device info
            self.logger.debug("Getting device info...")
            self._get_device_info()
            
            self.connected = True
            self.logger.info(f"ESP32 connected successfully on {self.port}")
            self.logger.info(f"Device ID: {self.device_id}, Firmware: {self.firmware_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to ESP32 on {self.port}: {e}", exc_info=True)
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from ESP32 device"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
        self.logger.info(f"ESP32 disconnected from {self.port}")
    
    def _send_command(self, command: str) -> Optional[str]:
        """Send command to ESP32 and get response"""
        if not self.connected or not self.serial:
            self.logger.warning("Cannot send command: not connected or no serial")
            return None
        
        try:
            # Clear any pending input before sending command
            self.serial.reset_input_buffer()
            
            # Send command
            cmd_bytes = f"{command}\n".encode()
            self.logger.debug(f"Sending command to ESP32: '{command}' ({len(cmd_bytes)} bytes)")
            bytes_written = self.serial.write(cmd_bytes)
            self.logger.debug(f"Wrote {bytes_written} bytes to ESP32")
            
            # Small delay to allow ESP32 to process
            time.sleep(0.05)
            
            # Read response (wait up to timeout)
            self.logger.debug(f"Waiting for response (timeout: {self.timeout}s)...")
            response = self.serial.readline().decode().strip()
            self.logger.debug(f"Received response from ESP32: '{response}' ({len(response)} chars)")
            
            if not response:
                self.logger.warning(f"Empty response from ESP32 for command '{command}'")
                return None
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}", exc_info=True)
            return None
    
    def _get_device_info(self):
        """Get device information from ESP32"""
        try:
            self.logger.debug("Requesting device info from ESP32...")
            response = self._send_command("INFO")
            if response:
                self.logger.debug(f"Device info response: {response}")
                # Parse JSON response if available
                try:
                    info = json.loads(response)
                    self.device_id = info.get("id", "ESP32")
                    self.firmware_version = info.get("version", "Unknown")
                    self.logger.info(f"Device info parsed: ID={self.device_id}, Version={self.firmware_version}")
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Could not parse device info as JSON: {e}. Response: {response}")
                    self.device_id = "ESP32"
                    self.firmware_version = "Unknown"
            else:
                self.logger.warning("No response from ESP32 for INFO command")
                self.device_id = "ESP32"
                self.firmware_version = "Unknown"
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}", exc_info=True)
            self.device_id = "ESP32"
            self.firmware_version = "Unknown"
    
    def read_ads1115(self, channel: int = ADS1115Channel.A0, 
                     gain: int = ADS1115Gain.GAIN_ONE) -> Optional[float]:
        """
        Read value from ADS1115 ADC
        
        Args:
            channel: Channel to read (0-7, see ADS1115Channel)
            gain: Gain setting (see ADS1115Gain)
        
        Returns:
            Raw ADC value or None if error
        """
        if not self.connected:
            self.logger.warning("Cannot read ADS1115: ESP32 not connected")
            return None
        
        try:
            # Send read command with channel and gain
            command = f"READ_ADS {channel} {gain}"
            self.logger.debug(f"Reading ADS1115: channel={channel}, gain={gain}")
            response = self._send_command(command)
            
            if response:
                self.logger.debug(f"ADS1115 response: '{response}'")
                # Parse response
                try:
                    # Expected format: "OK:12345" or just "12345"
                    if response.startswith("OK:"):
                        value_str = response.split(":")[1]
                    elif response.startswith("ERROR:"):
                        self.logger.error(f"ESP32 returned error: {response}")
                        return None
                    else:
                        value_str = response
                    
                    raw_value = float(value_str)
                    self.logger.debug(f"ADS1115 raw value: {raw_value}")
                    return raw_value
                    
                except (ValueError, IndexError) as e:
                    self.logger.error(f"Failed to parse ADS1115 response '{response}': {e}")
                    return None
            else:
                self.logger.warning("No response from ESP32 for READ_ADS command")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading ADS1115: {e}", exc_info=True)
            return None
    
    def read_ads1115_calibrated(self) -> Optional[float]:
        """Read ADS1115 with calibration applied"""
        self.logger.debug(f"Reading ADS1115 with calibration: channel={self.calibration.channel}, type={self.calibration.reading_type}")
        raw_value = self.read_ads1115(
            channel=self.calibration.channel,
            gain=ADS1115Gain.GAIN_ONE
        )
        
        if raw_value is not None:
            calibrated = self.calibration.convert_reading(raw_value)
            self.logger.debug(f"Calibrated value: raw={raw_value} -> calibrated={calibrated}")
            return calibrated
        else:
            self.logger.warning("Failed to read raw value from ADS1115")
        
        return None
    
    def set_calibration(self, calibration: ADS1115Calibration):
        """Set calibration for ADS1115 readings"""
        self.calibration = calibration
        self.logger.info(f"ADS1115 calibration updated: channel={calibration.channel}, "
                        f"type={calibration.reading_type}")


class ESP32Manager:
    """Manager for ESP32 devices"""
    
    def __init__(self):
        self.logger = get_logger()
        self.devices: Dict[str, ESP32Device] = {}
    
    @staticmethod
    def list_available_ports() -> List[Dict[str, str]]:
        """List available serial ports"""
        ports = []
        
        for port in serial.tools.list_ports.comports():
            port_info = {
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer or "Unknown",
                "product": port.product or "Unknown"
            }
            ports.append(port_info)
        
        return ports
    
    def connect_device(self, port: str, baudrate: int = 115200) -> Optional[ESP32Device]:
        """
        Connect to an ESP32 device
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0', 'COM3')
            baudrate: Baud rate for serial communication
        
        Returns:
            ESP32Device instance if successful, None otherwise
        """
        if port in self.devices:
            self.logger.warning(f"Device on {port} already connected")
            return self.devices[port]
        
        device = ESP32Device(port, baudrate)
        
        if device.connect():
            self.devices[port] = device
            self.logger.info(f"ESP32 device connected on {port}")
            return device
        
        return None
    
    def disconnect_device(self, port: str):
        """Disconnect ESP32 device"""
        if port in self.devices:
            self.devices[port].disconnect()
            del self.devices[port]
            self.logger.info(f"ESP32 device on {port} disconnected")
    
    def disconnect_all(self):
        """Disconnect all ESP32 devices"""
        for port in list(self.devices.keys()):
            self.disconnect_device(port)
    
    def get_device(self, port: str) -> Optional[ESP32Device]:
        """Get connected device by port"""
        return self.devices.get(port)
    
    def get_all_devices(self) -> List[ESP32Device]:
        """Get all connected devices"""
        return list(self.devices.values())


# Global manager instance
_esp32_manager = None


def get_esp32_manager() -> ESP32Manager:
    """Get global ESP32 manager instance"""
    global _esp32_manager
    if _esp32_manager is None:
        _esp32_manager = ESP32Manager()
    return _esp32_manager
