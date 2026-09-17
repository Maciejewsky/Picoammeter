# Directory Memory Feature

## Overview

All file dialogs in the measurement widgets now remember the last directory used, making it much easier to work with custom folders.

## How It Works

### Before This Feature:
```
User workflow:
1. Save measurement to custom folder: /home/user/experiment1/
2. Next save opens at: /home/user/keithley/exports/  ← Default folder
3. Navigate back to: /home/user/experiment1/        ← Annoying!
4. Repeat for every save...
```

### After This Feature:
```
User workflow:
1. Save measurement to custom folder: /home/user/experiment1/
2. Next save opens at: /home/user/experiment1/     ← Remembered!
3. Save immediately                                 ← Fast!
4. All subsequent saves open in the same place     ← Convenient!
```

## Implementation Details

### Class Variables
Each measurement block now has three class variables to track directories:
```python
class ResistanceMeasurementBlock(QWidget):
    # Class variables to remember last used directories
    _last_params_dir = None      # For Save/Load Parameters
    _last_export_dir = None      # For Export Measurement
    _last_load_dir = None        # For Load Measurement
```

### Per-Operation Memory
The system tracks three separate directory types:
1. **Parameters** (`_last_params_dir`): JSON configuration files
2. **Exports** (`_last_export_dir`): Exported measurement data
3. **Loads** (`_last_load_dir`): Loading previous measurements

This separation allows you to:
- Save parameters in one folder
- Export measurements in another folder
- Load old measurements from yet another folder

Each operation remembers its own last location.

### Shared Across Instances
The class variables are shared across all instances of the same widget type:
- All SMU 2450 Resistance widgets share the same memory
- All SMU 2450 IV widgets share the same memory
- All Pico 6487 Resistance widgets share the same memory
- All Pico 6487 IV widgets share the same memory

This means if you have multiple connections, they all benefit from the same directory memory.

## Example Usage Scenarios

### Scenario 1: Organizing Experiments by Folder
```
Experiment 1:
1. Navigate to: /home/user/experiments/exp1/
2. Save measurement → remembered
3. Take 10 more measurements → all save quickly to exp1/

Experiment 2:
1. Navigate to: /home/user/experiments/exp2/
2. Save measurement → now exp2/ is remembered
3. Take 10 more measurements → all save quickly to exp2/
```

### Scenario 2: Parameters vs Data
```
Your workflow:
1. Save parameters to: /home/user/configs/standard_config/
   → Parameters dialog remembers this

2. Export measurements to: /home/user/data/2024-11-08/
   → Export dialog remembers this

3. Load old measurement from: /home/user/archive/
   → Load dialog remembers this

Each operation opens in its respective last location!
```

### Scenario 3: Session Continuity
```
Throughout your session:
- First export: Navigate to custom folder once
- All subsequent exports: Open immediately in same folder
- Save time and avoid navigation errors
```

## Code Changes

### Before:
```python
def export_measurement(self):
    # Always uses default directory
    export_dir = self.user_manager.get_user_directory("exports")
    filename, _ = QFileDialog.getSaveFileName(
        self, "Exportar Medição", str(export_dir), "Text Files (*.txt)"
    )
```

### After:
```python
def export_measurement(self):
    # Uses last directory if available, otherwise default
    if ResistanceMeasurementBlock._last_export_dir:
        default_path = os.path.join(
            ResistanceMeasurementBlock._last_export_dir, 
            default_filename
        )
    else:
        export_dir = self.user_manager.get_user_directory("exports")
        default_path = str(export_dir / default_filename)
    
    filename, _ = QFileDialog.getSaveFileName(
        self, "Exportar Medição", default_path, "Text Files (*.txt)"
    )
    
    if filename:
        # Remember for next time!
        ResistanceMeasurementBlock._last_export_dir = os.path.dirname(filename)
```

## Benefits

✅ **Saves Time**: No need to navigate to the same folder repeatedly
✅ **Reduces Errors**: Less chance of saving to wrong location
✅ **Better UX**: More intuitive workflow
✅ **Flexible**: Each operation type has separate memory
✅ **Session-aware**: Memory persists throughout program session
✅ **Consistent**: Works the same across all 4 measurement widgets

## Limitations

⚠️ **Session-only**: Directory memory is reset when program restarts
⚠️ **No configuration**: Cannot manually set or clear remembered directories
⚠️ **Shared across widgets**: All instances of same widget type share memory

## Technical Notes

### Widget Types Affected
1. `widgets/smu_2450/block_resistance_time.py` - SMU 2450 Resistance
2. `widgets/smu_2450/block_iv_measurement.py` - SMU 2450 I-V
3. `widgets/pico_6487/block_resistance_time.py` - Pico 6487 Resistance
4. `widgets/pico_6487/block_iv_measurement.py` - Pico 6487 I-V

### Methods Updated (per widget)
- `save_parameters()` - Uses `_last_params_dir`
- `load_parameters()` - Uses `_last_params_dir`
- `export_measurement()` - Uses `_last_export_dir`
- `load_measurement()` - Uses `_last_load_dir`

### Fallback Behavior
If no directory has been remembered yet (first use), the system falls back to:
- **Parameters**: `users/{username}/configs/presets/`
- **Exports**: `users/{username}/exports/`
- **Loads**: `users/{username}/exports/`

## Future Enhancements (Not Implemented)

Possible improvements for future versions:
- 💾 Persist directory memory to disk (survives restart)
- 🔧 User preference to enable/disable per operation type
- 🗑️ UI to clear/reset remembered directories
- 📁 Per-user directory memory (stored in user profile)
- 🎯 Most-recently-used (MRU) list of directories

## Commit

Feature implemented in commit: `6e8ba56`

## Testing

To test this feature:
1. Open a measurement widget (e.g., Resistance)
2. Click "Exportar Medição"
3. Navigate to a custom folder (e.g., Documents/test/)
4. Save the file
5. Click "Exportar Medição" again
6. **Verify**: Dialog opens in Documents/test/ automatically! ✓

Repeat for:
- Save/Load Parameters
- Load Measurement
- All four widget types
