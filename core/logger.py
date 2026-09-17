"""
Logging system for Keithley LabNano3D
Provides comprehensive logging with file and console output
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LabNanoLogger:
    """Centralized logging system for the application"""
    
    def __init__(self, username=None):
        self.username = username or "default"
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory
        logs_dir = Path("logs") / self.username
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("LabNano3D")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for all logs
        log_file = logs_dir / f"labnano3d_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for info and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Set formatters
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized for user: {self.username}")
    
    def get_logger(self):
        """Get the configured logger"""
        return self.logger
    
    def log_instrument_command(self, instrument_id, command, response=None, error=None):
        """Log instrument communication"""
        if error:
            self.logger.error(f"[{instrument_id}] Command '{command}' failed: {error}")
        else:
            self.logger.debug(f"[{instrument_id}] Command '{command}' -> {response}")
    
    def log_measurement_start(self, measurement_type, parameters):
        """Log measurement start"""
        self.logger.info(f"Starting {measurement_type} measurement with parameters: {parameters}")
    
    def log_measurement_end(self, measurement_type, duration, data_points):
        """Log measurement completion"""
        self.logger.info(f"Completed {measurement_type} measurement in {duration:.2f}s, {data_points} data points")
    
    def log_user_action(self, action, details=None):
        """Log user actions"""
        msg = f"User action: {action}"
        if details:
            msg += f" - {details}"
        self.logger.info(msg)

# Global logger instance
_logger_instance = None

def get_logger(username=None):
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None or (username and _logger_instance.username != username):
        _logger_instance = LabNanoLogger(username)
    return _logger_instance.get_logger()

def init_logging(username):
    """Initialize logging for a specific user"""
    global _logger_instance
    _logger_instance = LabNanoLogger(username)
    return _logger_instance.get_logger()