"""
Database management for Keithley LabNano3D
Handles local SQLite database for measurement history, configurations, and data storage
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class MeasurementRecord:
    """Data class for measurement records"""
    id: str
    user_id: str
    instrument_name: str
    instrument_model: str
    measurement_type: str
    parameters: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    duration: Optional[float]
    data_points: int
    status: str  # 'running', 'completed', 'failed', 'cancelled'
    notes: str
    data_file_path: Optional[str]
    created_at: str
    updated_at: str


class DatabaseManager:
    """Manages the local SQLite database for the application"""
    
    def __init__(self, user_manager=None):
        self.user_manager = user_manager
        self.db_path = Path("database") / "labnano3d.db"
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    preferences TEXT
                )
            """)
            
            # Instruments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS instruments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    model TEXT NOT NULL,
                    manufacturer TEXT,
                    serial_number TEXT,
                    address TEXT NOT NULL,
                    instrument_type TEXT,
                    is_simulated BOOLEAN DEFAULT 0,
                    configuration TEXT,
                    created_at TEXT NOT NULL,
                    last_used TEXT
                )
            """)
            
            # Measurements table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    instrument_id TEXT,
                    measurement_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    parameters TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration REAL,
                    data_points INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'created',
                    notes TEXT,
                    data_file_path TEXT,
                    export_formats TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (instrument_id) REFERENCES instruments (id)
                )
            """)
            
            # Measurement data table (for storing actual measurement values)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS measurement_data (
                    id TEXT PRIMARY KEY,
                    measurement_id TEXT NOT NULL,
                    data_index INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id)
                )
            """)
            
            # Configuration presets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_presets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    measurement_type TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    description TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Exported files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exported_files (
                    id TEXT PRIMARY KEY,
                    measurement_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_format TEXT NOT NULL,
                    file_size INTEGER,
                    exported_at TEXT NOT NULL,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON measurements (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_measurements_start_time ON measurements (start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_measurement_data_measurement_id ON measurement_data (measurement_id)")
            
            conn.commit()
    
    def add_user(self, username: str, first_name: str, last_name: str, preferences: Dict = None) -> str:
        """Add a new user to the database"""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO users (id, username, first_name, last_name, created_at, last_login, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, now, now, json.dumps(preferences or {})))
            conn.commit()
        
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                user['preferences'] = json.loads(user['preferences']) if user['preferences'] else {}
                return user
        
        return None
    
    def update_user_login(self, username: str):
        """Update user's last login time"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
            conn.commit()
    
    def add_instrument(self, name: str, model: str, address: str, **kwargs) -> str:
        """Add an instrument to the database"""
        instrument_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO instruments (id, name, model, manufacturer, serial_number, address, 
                                       instrument_type, is_simulated, configuration, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instrument_id, name, model, kwargs.get('manufacturer', ''),
                kwargs.get('serial_number', ''), address, kwargs.get('instrument_type', ''),
                kwargs.get('is_simulated', False), json.dumps(kwargs.get('configuration', {})),
                now, now
            ))
            conn.commit()
        
        return instrument_id
    
    def get_instruments(self) -> List[Dict]:
        """Get all instruments"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM instruments ORDER BY last_used DESC")
            
            instruments = []
            for row in cursor.fetchall():
                instrument = dict(row)
                instrument['configuration'] = json.loads(instrument['configuration']) if instrument['configuration'] else {}
                instruments.append(instrument)
            
            return instruments
    
    def create_measurement(self, user_id: str, measurement_type: str, title: str = None, **kwargs) -> str:
        """Create a new measurement record"""
        measurement_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO measurements (id, user_id, instrument_id, measurement_type, title, description,
                                        parameters, start_time, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                measurement_id, user_id, kwargs.get('instrument_id'), measurement_type,
                title or f"{measurement_type} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                kwargs.get('description', ''), json.dumps(kwargs.get('parameters', {})),
                now, 'created', kwargs.get('notes', ''), now, now
            ))
            conn.commit()
        
        return measurement_id
    
    def start_measurement(self, measurement_id: str):
        """Mark measurement as started"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE measurements 
                SET status = 'running', start_time = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, measurement_id))
            conn.commit()
    
    def complete_measurement(self, measurement_id: str, data_points: int = 0, data_file_path: str = None):
        """Mark measurement as completed"""
        now = datetime.now().isoformat()
        
        # Calculate duration
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT start_time FROM measurements WHERE id = ?", (measurement_id,))
            row = cursor.fetchone()
            
            duration = None
            if row and row[0]:
                start_time = datetime.fromisoformat(row[0])
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
            
            conn.execute("""
                UPDATE measurements 
                SET status = 'completed', end_time = ?, duration = ?, data_points = ?, 
                    data_file_path = ?, updated_at = ?
                WHERE id = ?
            """, (now, duration, data_points, data_file_path, now, measurement_id))
            conn.commit()
    
    def add_measurement_data_point(self, measurement_id: str, data_index: int, data: Dict[str, Any]):
        """Add a single data point to measurement"""
        data_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO measurement_data (id, measurement_id, data_index, timestamp, data_json)
                VALUES (?, ?, ?, ?, ?)
            """, (data_id, measurement_id, data_index, now, json.dumps(data)))
            conn.commit()
    
    def get_measurements(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get measurements, optionally filtered by user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if user_id:
                cursor = conn.execute("""
                    SELECT m.*, i.name as instrument_name, i.model as instrument_model
                    FROM measurements m
                    LEFT JOIN instruments i ON m.instrument_id = i.id
                    WHERE m.user_id = ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT m.*, i.name as instrument_name, i.model as instrument_model,
                           u.first_name, u.last_name
                    FROM measurements m
                    LEFT JOIN instruments i ON m.instrument_id = i.id
                    LEFT JOIN users u ON m.user_id = u.id
                    ORDER BY m.created_at DESC
                    LIMIT ?
                """, (limit,))
            
            measurements = []
            for row in cursor.fetchall():
                measurement = dict(row)
                measurement['parameters'] = json.loads(measurement['parameters']) if measurement['parameters'] else {}
                measurements.append(measurement)
            
            return measurements
    
    def get_measurement_data(self, measurement_id: str) -> List[Dict]:
        """Get all data points for a measurement"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM measurement_data 
                WHERE measurement_id = ? 
                ORDER BY data_index
            """, (measurement_id,))
            
            data_points = []
            for row in cursor.fetchall():
                point = dict(row)
                point['data'] = json.loads(point['data_json'])
                del point['data_json']  # Remove the raw JSON
                data_points.append(point)
            
            return data_points
    
    def save_configuration_preset(self, user_id: str, name: str, measurement_type: str, 
                                 parameters: Dict, description: str = None) -> str:
        """Save a configuration preset"""
        preset_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO configuration_presets (id, user_id, name, measurement_type, parameters,
                                                  description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (preset_id, user_id, name, measurement_type, json.dumps(parameters), 
                  description or '', now, now))
            conn.commit()
        
        return preset_id
    
    def get_configuration_presets(self, user_id: str, measurement_type: str = None) -> List[Dict]:
        """Get configuration presets for a user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if measurement_type:
                cursor = conn.execute("""
                    SELECT * FROM configuration_presets 
                    WHERE user_id = ? AND measurement_type = ?
                    ORDER BY is_default DESC, name
                """, (user_id, measurement_type))
            else:
                cursor = conn.execute("""
                    SELECT * FROM configuration_presets 
                    WHERE user_id = ?
                    ORDER BY measurement_type, is_default DESC, name
                """, (user_id,))
            
            presets = []
            for row in cursor.fetchall():
                preset = dict(row)
                preset['parameters'] = json.loads(preset['parameters'])
                presets.append(preset)
            
            return presets
    
    def export_measurement_to_csv(self, measurement_id: str, file_path: str) -> bool:
        """Export measurement data to CSV file"""
        try:
            # Get measurement info
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT m.*, i.name as instrument_name, i.model as instrument_model,
                           u.first_name, u.last_name
                    FROM measurements m
                    LEFT JOIN instruments i ON m.instrument_id = i.id
                    LEFT JOIN users u ON m.user_id = u.id
                    WHERE m.id = ?
                """, (measurement_id,))
                measurement = dict(cursor.fetchone())
                measurement['parameters'] = json.loads(measurement['parameters']) if measurement['parameters'] else {}
            
            # Get measurement data
            data_points = self.get_measurement_data(measurement_id)
            
            if not data_points:
                return False
            
            # Convert to DataFrame
            df_data = []
            for point in data_points:
                row = {
                    'index': point['data_index'],
                    'timestamp': point['timestamp'],
                    **point['data']
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Add metadata as comments
            metadata_lines = [
                f"# Measurement: {measurement['title']}",
                f"# Type: {measurement['measurement_type']}",
                f"# Instrument: {measurement.get('instrument_name', 'N/A')} ({measurement.get('instrument_model', 'N/A')})",
                f"# User: {measurement.get('first_name', '')} {measurement.get('last_name', '')}",
                f"# Start Time: {measurement['start_time']}",
                f"# End Time: {measurement.get('end_time', 'N/A')}",
                f"# Duration: {measurement.get('duration', 'N/A')} seconds",
                f"# Data Points: {measurement['data_points']}",
                f"# Parameters: {json.dumps(measurement['parameters'], indent=2)}",
                f"# Notes: {measurement.get('notes', 'N/A')}",
                "#",
            ]
            
            # Write file with metadata
            with open(file_path, 'w') as f:
                for line in metadata_lines:
                    f.write(line + '\n')
                df.to_csv(f, index=False)
            
            # Record export
            self.record_export(measurement_id, file_path, 'csv')
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def record_export(self, measurement_id: str, file_path: str, file_format: str):
        """Record an export operation"""
        export_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Get file size
        try:
            file_size = Path(file_path).stat().st_size
        except:
            file_size = 0
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO exported_files (id, measurement_id, file_path, file_format, file_size, exported_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (export_id, measurement_id, file_path, file_format, file_size, now))
            conn.commit()
    
    def get_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Total measurements
            if user_id:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements WHERE user_id = ?", (user_id,))
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements")
            stats['total_measurements'] = cursor.fetchone()[0]
            
            # Completed measurements
            if user_id:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements WHERE user_id = ? AND status = 'completed'", (user_id,))
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements WHERE status = 'completed'")
            stats['completed_measurements'] = cursor.fetchone()[0]
            
            # Total data points
            if user_id:
                cursor = conn.execute("""
                    SELECT SUM(data_points) FROM measurements 
                    WHERE user_id = ? AND data_points IS NOT NULL
                """, (user_id,))
            else:
                cursor = conn.execute("SELECT SUM(data_points) FROM measurements WHERE data_points IS NOT NULL")
            result = cursor.fetchone()[0]
            stats['total_data_points'] = result if result else 0
            
            # Total instruments
            cursor = conn.execute("SELECT COUNT(*) FROM instruments")
            stats['total_instruments'] = cursor.fetchone()[0]
            
            # Total users
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            return stats


# Global database manager instance
_db_manager = None

def get_database_manager(user_manager=None) -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(user_manager)
    return _db_manager