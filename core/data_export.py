"""
Data export system for Keithley LabNano3D
Handles CSV export with comprehensive metadata
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def export_measurement_data(
    #file_path: str,
    file_path: "C:\Users\lucia\OneDrive\Ellem\Mestrado\Dissertacao\Sensor Grade Protótipo\Produção dos Substratos",
    measurement_type: str,
    data: List[List[Any]],
    headers: List[str],
    user_name: str,
    instrument_info: Dict[str, str],
    measurement_params: Dict[str, Any]
) -> bool:
    """
    Export measurement data to CSV with comprehensive metadata
    
    Args:
        file_path: Full path to save CSV file
        measurement_type: Type of measurement (e.g., "Resistência", "Curva I-V")
        data: List of data rows
        headers: Column headers
        user_name: Full name of user
        instrument_info: Dict with 'model', 'serial', 'address'
        measurement_params: Dict with measurement parameters
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # Write metadata header
            f.write(f"# Keithley LabNano3D - Medição de {measurement_type}\n")
            f.write(f"# Usuário: {user_name}\n")
            f.write(f"# Equipamento: {instrument_info.get('model', 'N/A')} "
                   f"(Serial: {instrument_info.get('serial', 'N/A')})\n")
            f.write(f"# Endereço: {instrument_info.get('address', 'N/A')}\n")
            f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Write measurement parameters
            if measurement_params:
                f.write("#\n# Parâmetros de Medição:\n")
                for key, value in measurement_params.items():
                    f.write(f"# {key}: {value}\n")
            
            f.write("# ---\n")
            
            # Write data using CSV writer
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        
        return True
    
    except Exception as e:
        print(f"Error exporting data: {e}")
        return False


def import_measurement_data(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Import measurement data from CSV file
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        Dict with 'metadata', 'headers', 'data' or None if failed
    """
    try:
        metadata = {}
        headers = []
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read metadata
            for line in f:
                if line.startswith('# ---'):
                    break
                elif line.startswith('#'):
                    # Parse metadata
                    line = line[1:].strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            
            # Read CSV data
            reader = csv.reader(f)
            headers = next(reader, [])
            data = list(reader)
        
        return {
            'metadata': metadata,
            'headers': headers,
            'data': data
        }
    
    except Exception as e:
        print(f"Error importing data: {e}")
        return None


def get_measurement_type_from_file(file_path: str) -> Optional[str]:
    """
    Determine measurement type from CSV file metadata
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        Measurement type string or None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if 'Resistência' in first_line:
                return 'resistance'
            elif 'Curva I-V' in first_line or 'I-V' in first_line:
                return 'iv'
            elif 'Corrente' in first_line:
                return 'current'
    except:
        pass
    
    return None


def filter_files_by_type(directory: Path, measurement_type: str) -> List[Path]:
    """
    Filter CSV files in directory by measurement type
    
    Args:
        directory: Directory to search
        measurement_type: Type to filter ('resistance', 'iv', 'current')
    
    Returns:
        List of matching file paths
    """
    matching_files = []
    
    if not directory.exists():
        return matching_files
    
    for file_path in directory.glob("*.csv"):
        file_type = get_measurement_type_from_file(str(file_path))
        if file_type == measurement_type:
            matching_files.append(file_path)
    
    return matching_files
