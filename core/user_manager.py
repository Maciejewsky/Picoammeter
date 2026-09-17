"""
User management system for Keithley LabNano3D
Handles user profiles, data directories, and session management
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class UserManager:
    """Manages user profiles and data directories"""
    
    def __init__(self):
        self.users_dir = Path("users")
        self.users_dir.mkdir(exist_ok=True)
        self.current_user = None
        self.user_data = {}
    
    def create_user_profile(self, first_name: str, last_name: str) -> str:
        """Create a new user profile or load existing one"""
        # Generate username from names
        username = f"{first_name.lower()}_{last_name.lower()}"
        user_dir = self.users_dir / username
        
        # Create user directory structure
        user_dir.mkdir(exist_ok=True)
        (user_dir / "measurements").mkdir(exist_ok=True)
        (user_dir / "measurements" / "resistance").mkdir(exist_ok=True)
        (user_dir / "measurements" / "current").mkdir(exist_ok=True)
        (user_dir / "measurements" / "iv").mkdir(exist_ok=True)
        (user_dir / "scripts").mkdir(exist_ok=True)
        (user_dir / "scripts" / "smu_2450").mkdir(exist_ok=True)
        (user_dir / "scripts" / "pico_6487").mkdir(exist_ok=True)
        (user_dir / "exports").mkdir(exist_ok=True)
        (user_dir / "configs").mkdir(exist_ok=True)
        (user_dir / "configs" / "presets").mkdir(exist_ok=True)
        
        # User profile data
        profile_file = user_dir / "profile.json"
        profile_data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "created_date": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "preferences": {
                "theme": "light",
                "auto_save": True,
                "default_export_format": "csv",
                "graph_style": "modern"
            }
        }
        
        # Load existing profile or create new one
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                existing_data = json.load(f)
                existing_data["last_login"] = datetime.now().isoformat()
                profile_data = existing_data
        
        # Save profile
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        self.current_user = username
        self.user_data = profile_data
        
        return username
    
    def get_user_directory(self, subdirectory: str = None) -> Path:
        """Get user's directory path"""
        if not self.current_user:
            raise ValueError("No user logged in")
        
        base_dir = self.users_dir / self.current_user
        if subdirectory:
            return base_dir / subdirectory
        return base_dir
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference value"""
        if not self.user_data:
            return default
        return self.user_data.get("preferences", {}).get(key, default)
    
    def set_user_preference(self, key: str, value: Any):
        """Set user preference value"""
        if not self.current_user:
            return
        
        if "preferences" not in self.user_data:
            self.user_data["preferences"] = {}
        
        self.user_data["preferences"][key] = value
        
        # Save to file
        profile_file = self.get_user_directory() / "profile.json"
        with open(profile_file, 'w') as f:
            json.dump(self.user_data, f, indent=2)
    
    def get_current_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        return self.user_data.copy() if self.user_data else {}
    
    def list_users(self) -> list:
        """List all registered users"""
        users = []
        for user_dir in self.users_dir.iterdir():
            if user_dir.is_dir():
                profile_file = user_dir / "profile.json"
                if profile_file.exists():
                    try:
                        with open(profile_file, 'r') as f:
                            profile = json.load(f)
                            users.append({
                                "username": profile.get("username"),
                                "first_name": profile.get("first_name"),
                                "last_name": profile.get("last_name"),
                                "last_login": profile.get("last_login")
                            })
                    except Exception:
                        continue
        return users
    
    def login_user(self, username: str) -> bool:
        """Login existing user"""
        user_dir = self.users_dir / username
        profile_file = user_dir / "profile.json"
        
        if profile_file.exists():
            try:
                with open(profile_file, 'r') as f:
                    self.user_data = json.load(f)
                    self.user_data["last_login"] = datetime.now().isoformat()
                
                # Update last login
                with open(profile_file, 'w') as f:
                    json.dump(self.user_data, f, indent=2)
                
                self.current_user = username
                return True
            except Exception:
                pass
        
        return False

# Global user manager instance
_user_manager = None

def get_user_manager() -> UserManager:
    """Get the global user manager instance"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager