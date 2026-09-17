"""
Configuration management for Keithley LabNano3D
Handles application settings, instrument configurations, and user preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class InstrumentConfig:
    """Configuration for a specific instrument"""
    name: str
    model: str
    address: str
    timeout: int = 5000
    read_termination: str = "\r"
    write_termination: str = "\n"
    auto_reconnect: bool = True
    max_retries: int = 3

@dataclass
class MeasurementConfig:
    """Configuration for measurement parameters"""
    measurement_type: str
    parameters: Dict[str, Any]
    auto_save: bool = True
    export_format: str = "csv"
    include_metadata: bool = True

@dataclass
class AppConfig:
    """Main application configuration"""
    debug_mode: bool = False
    debug_password: str = "debug123"
    theme: str = "light"
    language: str = "pt_BR"
    auto_detect_instruments: bool = True
    max_instruments: int = 4
    data_backup_enabled: bool = True
    log_level: str = "INFO"

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self, user_manager=None):
        self.user_manager = user_manager
        self.app_config = AppConfig()
        self.instrument_configs = {}
        self.measurement_configs = {}
        self.config_file = Path("config") / "app_config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load app config
                    if "app_config" in data:
                        app_data = data["app_config"]
                        for key, value in app_data.items():
                            if hasattr(self.app_config, key):
                                setattr(self.app_config, key, value)
                    
                    # Load instrument configs
                    if "instrument_configs" in data:
                        for name, config_data in data["instrument_configs"].items():
                            self.instrument_configs[name] = InstrumentConfig(**config_data)
                    
                    # Load measurement configs
                    if "measurement_configs" in data:
                        for name, config_data in data["measurement_configs"].items():
                            self.measurement_configs[name] = MeasurementConfig(**config_data)
        
        except Exception as e:
            print(f"Error loading config: {e}")
            # Use defaults
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config_data = {
                "app_config": asdict(self.app_config),
                "instrument_configs": {
                    name: asdict(config) for name, config in self.instrument_configs.items()
                },
                "measurement_configs": {
                    name: asdict(config) for name, config in self.measurement_configs.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration"""
        return self.app_config
    
    def update_app_config(self, **kwargs):
        """Update application configuration"""
        for key, value in kwargs.items():
            if hasattr(self.app_config, key):
                setattr(self.app_config, key, value)
        self.save_config()
    
    def add_instrument_config(self, name: str, config: InstrumentConfig):
        """Add instrument configuration"""
        self.instrument_configs[name] = config
        self.save_config()
    
    def get_instrument_config(self, name: str) -> Optional[InstrumentConfig]:
        """Get instrument configuration"""
        return self.instrument_configs.get(name)
    
    def remove_instrument_config(self, name: str):
        """Remove instrument configuration"""
        if name in self.instrument_configs:
            del self.instrument_configs[name]
            self.save_config()
    
    def list_instrument_configs(self) -> Dict[str, InstrumentConfig]:
        """List all instrument configurations"""
        return self.instrument_configs.copy()
    
    def add_measurement_config(self, name: str, config: MeasurementConfig):
        """Add measurement configuration"""
        self.measurement_configs[name] = config
        self.save_config()
    
    def get_measurement_config(self, name: str) -> Optional[MeasurementConfig]:
        """Get measurement configuration"""
        return self.measurement_configs.get(name)
    
    def list_measurement_configs(self) -> Dict[str, MeasurementConfig]:
        """List all measurement configurations"""
        return self.measurement_configs.copy()
    
    def verify_debug_password(self, password: str) -> bool:
        """Verify debug mode password"""
        return password == self.app_config.debug_password
    
    def get_user_config_file(self) -> Optional[Path]:
        """Get user-specific config file path"""
        if self.user_manager and self.user_manager.current_user:
            user_dir = self.user_manager.get_user_directory("configs")
            return user_dir / "user_config.json"
        return None
    
    def load_user_config(self):
        """Load user-specific configuration"""
        config_file = self.get_user_config_file()
        if config_file and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    
                    # Override app config with user preferences
                    if "preferences" in user_config:
                        for key, value in user_config["preferences"].items():
                            if hasattr(self.app_config, key):
                                setattr(self.app_config, key, value)
            
            except Exception as e:
                print(f"Error loading user config: {e}")
    
    def save_user_config(self):
        """Save user-specific configuration"""
        config_file = self.get_user_config_file()
        if config_file:
            try:
                user_config = {
                    "preferences": {
                        "theme": self.app_config.theme,
                        "language": self.app_config.language,
                        "auto_detect_instruments": self.app_config.auto_detect_instruments,
                        "data_backup_enabled": self.app_config.data_backup_enabled,
                        "log_level": self.app_config.log_level
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(user_config, f, indent=2)
            
            except Exception as e:
                print(f"Error saving user config: {e}")

# Global config manager instance
_config_manager = None

def get_config_manager(user_manager=None) -> ConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(user_manager)
    return _config_manager