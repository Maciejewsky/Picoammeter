"""
Combined Measurement Widget for Instrument + ESP32
Based on single instrument resistance measurement widget, extends it with ESP32/ADS1115 readings
Follows the same layout and methods as single VISA instrument measurements
"""

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import json
import os

from core.logger import get_logger


class CombinedMeasurementWidget(QWidget):
    """Widget for combined VISA instrument + ESP32 measurements
    Extends single instrument functionality by adding ESP32 readings"""
    
    # Class variables to remember last used directories (same as ResistanceMeasurementBlock)
    _last_params_dir = None
    _last_export_dir = None
    _last_load_dir = None
    
    def __init__(self, visa_instrument, esp32_device, device_type="smu_2450", user_manager=None, parent=None):
        super().__init__(parent)
        
        self.instrument = visa_instrument  # Use same name as single instrument
        self.esp32_device = esp32_device
        self.device_type = device_type  # Store device type to use appropriate commands
        self.user_manager = user_manager
        self.logger = get_logger()
        
        # Measurement data - using same structure as single instrument but with ESP32 column
        self.readings = []  # List of tuples (time_s, resistance, esp32_value)
        self.start_time = None
        self.first_reading_time = None
        self.last_buffer_index = 0
        self.temp_file_path = None
        
        # Measurement state
        self.measuring = False
        self.config_step = 0  # For Picoammeter sequential configuration
        
        # Timer for measurements - same as single instrument
        self.measure_timer = QTimer()
        self.measure_timer.timeout.connect(self.acquire_reading)
        
        self.logger.info(f"Combined measurement widget initialized for device type: {device_type}")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI following single instrument layout pattern"""
        # Use splitter layout like single instrument widgets
        splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)
        
        # ----- Left side: Controls (same structure as single instrument) -----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Parameters group
        params_group = QGroupBox("Parâmetros de Medição")
        params_layout = QVBoxLayout()
        
        # VISA instrument parameters (same as single instrument)
        hlayout_v = QHBoxLayout()
        hlayout_v.addWidget(QLabel("Tensão (V):"))
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(-210, 210)
        self.voltage_spin.setDecimals(3)
        self.voltage_spin.setValue(1.0)
        hlayout_v.addWidget(self.voltage_spin)
        params_layout.addLayout(hlayout_v)
        
        # Current limit (same as single instrument)
        hlayout_ilim = QHBoxLayout()
        hlayout_ilim.addWidget(QLabel("Limite de corrente (A):"))
        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(1e-9, 1.0)
        self.ilim_spin.setDecimals(9)
        self.ilim_spin.setValue(1e-3)
        self.ilim_spin.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        hlayout_ilim.addWidget(self.ilim_spin)
        params_layout.addLayout(hlayout_ilim)
        
        # NPLC (same as single instrument)
        hlayout_nplc = QHBoxLayout()
        hlayout_nplc.addWidget(QLabel("NPLC:"))
        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.01, 10.0)
        self.nplc_spin.setDecimals(2)
        self.nplc_spin.setValue(1.0)
        hlayout_nplc.addWidget(self.nplc_spin)
        params_layout.addLayout(hlayout_nplc)
        
        # Measurement interval (same as single instrument)
        hlayout_t = QHBoxLayout()
        hlayout_t.addWidget(QLabel("Intervalo (s):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 60)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setValue(1.0)
        hlayout_t.addWidget(self.interval_spin)
        params_layout.addLayout(hlayout_t)
        
        # ESP32 info label (NEW - shows ESP32 is being used)
        esp32_label = f"ESP32: {self.esp32_device.calibration.label}" if self.esp32_device.calibration else "ESP32: Conectado"
        esp32_info = QLabel(f"📡 {esp32_label}")
        esp32_info.setStyleSheet("color: #FF9800; font-weight: bold; padding: 5px; background-color: #FFF3E0; border-radius: 3px;")
        params_layout.addWidget(esp32_info)
        
        # Save/Load parameter buttons (same as single instrument)
        params_buttons = QHBoxLayout()
        save_params_btn = QPushButton("Salvar Parâmetros")
        save_params_btn.clicked.connect(self.save_parameters)
        params_buttons.addWidget(save_params_btn)
        
        load_params_btn = QPushButton("Carregar Parâmetros")
        load_params_btn.clicked.connect(self.load_parameters)
        params_buttons.addWidget(load_params_btn)
        params_layout.addLayout(params_buttons)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        # Start/Stop button (same as single instrument)
        self.toggle_button = QPushButton("Iniciar Medição")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_measurement)
        left_layout.addWidget(self.toggle_button)
        
        # Readings list (same as single instrument)
        self.list_widget = QListWidget()
        left_layout.addWidget(self.list_widget)
        
        # Statistics label (same as single instrument)
        self.stats_label = QLabel("Total de leituras: 0 | Tempo: 00:00:00")
        left_layout.addWidget(self.stats_label)
        
        # Action buttons (same as single instrument)
        buttons_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Exportar Medição")
        self.export_button.clicked.connect(self.export_measurement)
        buttons_layout.addWidget(self.export_button)
        
        load_measurement_btn = QPushButton("Carregar Medição")
        load_measurement_btn.clicked.connect(self.load_measurement)
        buttons_layout.addWidget(load_measurement_btn)
        
        left_layout.addLayout(buttons_layout)
        
        splitter.addWidget(left_widget)
        
        # ----- Right side: Plot with dual Y-axes -----
        self.setup_plot_dual_axes()
        splitter.addWidget(self.plot_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
    
    def setup_plot_dual_axes(self):
        """Setup plot widget with dual Y-axes for VISA and ESP32"""
        self.plot_widget = pg.PlotWidget(title="Resistência vs Tempo (VISA + ESP32)")
        self.plot_widget.setLabel('left', 'Resistência (Ω)', color='#2196F3')
        self.plot_widget.setLabel('bottom', 'Tempo (s)')
        self.plot_widget.getAxis('left').setPen('#2196F3')
        
        # VISA curve (primary axis)
        self.curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='#2196F3', width=2), name='VISA')
        
        # Create secondary Y-axis for ESP32
        self.view_box2 = pg.ViewBox()
        self.plot_widget.scene().addItem(self.view_box2)
        self.plot_widget.getAxis('right').linkToView(self.view_box2)
        self.view_box2.setXLink(self.plot_widget)
        
        # Label for secondary axis
        esp32_unit = self.esp32_device.calibration.unit if self.esp32_device.calibration else "bits"
        esp32_label = self.esp32_device.calibration.label if self.esp32_device.calibration else "ESP32"
        self.plot_widget.setLabel('right', esp32_label, units=esp32_unit, color='#FF9800')
        self.plot_widget.getAxis('right').setPen('#FF9800')
        self.plot_widget.showAxis('right')
        
        # ESP32 curve (secondary axis)
        self.esp32_curve = pg.PlotCurveItem(pen=pg.mkPen(color='#FF9800', width=2), name='ESP32')
        self.view_box2.addItem(self.esp32_curve)
        
        # Update views when plot is resized
        def update_views():
            self.view_box2.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.view_box2.linkedViewChanged(self.plot_widget.getViewBox(), self.view_box2.XAxis)
        
        update_views()
        self.plot_widget.getViewBox().sigResized.connect(update_views)
        
        # Add legend
        self.plot_widget.addLegend()
    
    # ----- Measurement control methods (same pattern as single instrument) -----
    def toggle_measurement(self, checked):
        if checked:
            self.start_measurement()
        else:
            self.stop_measurement()
    
    def start_measurement(self):
        self.measuring = True
        self.readings.clear()
        self.list_widget.clear()
        self.start_time = datetime.now()
        self.first_reading_time = None
        self.last_buffer_index = 0
        self.config_step = 0
        self.toggle_button.setText("Parar Medição")
        self.curve.setData([], [])
        self.esp32_curve.setData([], [])
        
        # Create temporary file for auto-save
        if self.user_manager:
            temp_dir = self.user_manager.get_user_directory("measurements/combined")
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            self.temp_file_path = temp_dir / f"temp_combined_{timestamp}.txt"
        else:
            self.temp_file_path = None
        
        self.logger.info(f"Starting combined measurement with {self.device_type}")
        
        # Configure instrument based on device type
        if self.device_type == "pico_6487" or "6487" in str(self.device_type):
            self.logger.info("Configuring Picoammeter 6487 for combined measurement")
            self.configure_picoammeter_step(0)
        else:
            # SMU 2450 or other SMU-type devices
            self.logger.info("Configuring SMU 2450 for combined measurement")
            self.configure_smu()
    
    def configure_smu(self):
        """Configure SMU 2450 for measurement"""
        try:
            self.logger.info("SMU Configuration - Step 1: Reset")
            self.instrument.write("reset()")
            self.logger.info("SMU Configuration - Step 2: Set source function")
            self.instrument.write("smu.source.func = smu.FUNC_DC_VOLTAGE")
            self.logger.info(f"SMU Configuration - Step 3: Set current limit to {self.ilim_spin.value()}")
            self.instrument.write(f"smu.source.ilimit.level = {self.ilim_spin.value()}")
            self.logger.info(f"SMU Configuration - Step 4: Set voltage to {self.voltage_spin.value()}")
            self.instrument.write(f"smu.source.level = {self.voltage_spin.value()}")
            self.logger.info("SMU Configuration - Step 5: Set measure unit to OHM")
            self.instrument.write("smu.measure.unit = smu.UNIT_OHM")
            self.logger.info("SMU Configuration - Step 6: Set terminals to FRONT")
            self.instrument.write("smu.measure.terminals = smu.TERMINALS_FRONT")
            self.logger.info("SMU Configuration - Step 7: Enable autorange")
            self.instrument.write("smu.measure.autorange = smu.ON")
            self.logger.info(f"SMU Configuration - Step 8: Set NPLC to {self.nplc_spin.value()}")
            self.instrument.write(f"smu.measure.nplc = {self.nplc_spin.value()}")
            self.logger.info("SMU Configuration - Step 9: Turn output ON")
            self.instrument.write("smu.source.output = smu.ON")
            self.logger.info("SMU VISA instrument configured for combined measurement")
            
            # Start timer with same interval as single instrument
            interval_ms = int(self.interval_spin.value() * 1000)
            self.measure_timer.start(interval_ms)
            self.logger.info(f"Combined measurement timer started with interval: {interval_ms}ms")
        except Exception as e:
            self.logger.error(f"Error configuring SMU VISA instrument: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao configurar instrumento VISA:\n{e}")
            self.stop_measurement()
            return
    
    def configure_picoammeter_step(self, step):
        """Configure Picoammeter 6487 in steps (sequential with delays)"""
        v_resist = self.voltage_spin.value()
        i_limit = self.ilim_spin.value()
        nplc = self.nplc_spin.value()
        
        if abs(v_resist) <= 10:
            r_rang = 10
        elif abs(v_resist) <= 50:
            r_rang = 50
        else:
            r_rang = 500
        
        try:
            commands = [
                "*RST",
                "FORM:ELEM READ",
                "SYST:ZCH ON",
                f"SENS:CURR:NPLC {nplc}",
                "RANG 2e-9",
                "INIT",
                "SYST:ZCOR:STAT OFF",
                "SYST:ZCOR:ACQ",
                "SYST:ZCH OFF",
                "SYST:ZCOR ON",
                "SYST:ZCH ON",
                "RANG:AUTO ON",
                f"SOUR:VOLT:RANG {r_rang}",
                f"SOUR:VOLT {v_resist}",
                f"SOUR:VOLT:ILIM {i_limit}",
                "SENS:OHMS ON",
                "SOUR:VOLT:STAT ON",
                "SYST:ZCH OFF",
            ]
            
            if step < len(commands):
                self.logger.info(f"Picoammeter Configuration - Step {step+1}/{len(commands)}: {commands[step]}")
                self.instrument.write(commands[step])
                # Schedule next step in 200ms
                QTimer.singleShot(200, lambda: self.configure_picoammeter_step(step + 1))
            else:
                # Configuration complete, start measurements
                self.logger.info("Picoammeter configuration complete, starting measurement timer")
                interval_ms = int(self.interval_spin.value() * 1000)
                self.measure_timer.start(interval_ms)
                self.logger.info(f"Combined measurement timer started with interval: {interval_ms}ms")
        
        except Exception as e:
            self.logger.error(f"Error configuring Picoammeter at step {step}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Erro ao configurar Picoammeter (passo {step}):\n{e}")
            self.stop_measurement()
    
    def stop_measurement(self):
        self.measuring = False
        self.measure_timer.stop()
        self.toggle_button.setText("Iniciar Medição")
        if self.instrument:
            try:
                if self.device_type == "pico_6487" or "6487" in str(self.device_type):
                    self.logger.info("Turning off Picoammeter output")
                    self.instrument.write("SOUR:VOLT:STAT OFF")
                else:
                    self.logger.info("Turning off SMU output")
                    self.instrument.write("smu.source.output = smu.OFF")
                self.logger.info("VISA instrument output turned off")
            except Exception as e:
                self.logger.error(f"Error turning off VISA instrument: {e}")
        self.logger.info("Combined measurement stopped")
    
    def acquire_reading(self):
        """Acquire reading from both VISA and ESP32 simultaneously"""
        if not self.measuring or self.instrument is None:
            return
        
        try:
            self.logger.debug("Acquiring VISA reading...")
            # Measure from VISA instrument based on device type
            if self.device_type == "pico_6487" or "6487" in str(self.device_type):
                resistance = float(self.instrument.query("READ?"))
                self.logger.debug(f"Picoammeter reading: {resistance}")
            else:
                resistance = float(self.instrument.query("print(smu.measure.read())"))
                self.logger.debug(f"SMU reading: {resistance}")
            
            # Measure from ESP32
            self.logger.debug("Acquiring ESP32 reading...")
            esp32_reading = self.esp32_device.read_ads1115_calibrated()
            if esp32_reading is None:
                self.logger.warning("Failed to read from ESP32")
                esp32_reading = 0.0
            else:
                self.logger.debug(f"ESP32 reading: {esp32_reading}")
            
            if self.first_reading_time is None:
                self.first_reading_time = datetime.now()
            
            relative_time = (datetime.now() - self.start_time).total_seconds()
            
            # Store reading with ESP32 value (extend single instrument tuple)
            self.readings.append((relative_time, resistance, esp32_reading))
            self.logger.debug(f"Reading stored: time={relative_time:.2f}s, resistance={resistance}, esp32={esp32_reading}")
            
            # Auto-save to temporary file
            self.auto_save_reading(relative_time, resistance, esp32_reading)
            
            self.update_display()
            
        except Exception as e:
            self.logger.error(f"Error during measurement: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro de Medição", f"Erro durante medição:\n{e}\n\nMedição será parada.")
            self.stop_measurement()
    
    def auto_save_reading(self, time, resistance, esp32_value):
        """Auto-save reading to temporary file (extends single instrument method)"""
        if not self.temp_file_path:
            return
        
        try:
            # Create file with header if it doesn't exist
            if not os.path.exists(self.temp_file_path):
                with open(self.temp_file_path, 'w') as f:
                    f.write(f"# Auto-save temporário - Medição Combinada (VISA + ESP32)\n")
                    f.write(f"# Início: {self.start_time}\n")
                    f.write(f"# Tensão (V): {self.voltage_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
                    esp32_unit = self.esp32_device.calibration.unit if self.esp32_device.calibration else "bits"
                    esp32_label = self.esp32_device.calibration.label if self.esp32_device.calibration else "ESP32"
                    f.write(f"Tempo_(s)\tResistencia_(Ohms)\t{esp32_label}_({esp32_unit})\n")
            
            # Append reading
            with open(self.temp_file_path, 'a') as f:
                f.write(f"{time:.2f}\t{resistance:.6e}\t{esp32_value:.6f}\n")
        except Exception as e:
            self.logger.error(f"Error auto-saving: {e}")
    
    def update_display(self):
        """Update display with new readings (extends single instrument method)"""
        if self.readings:
            t, val, esp32_val = self.readings[-1]
            # Display both values in list
            esp32_unit = self.esp32_device.calibration.unit if self.esp32_device.calibration else "bits"
            self.list_widget.addItem(f"{t:.2f} s | {self.format_number(val)} Ω | ESP32: {esp32_val:.2f} {esp32_unit}")
            self.list_widget.scrollToBottom()
            
            elapsed_str = str(timedelta(seconds=int(t)))
            self.stats_label.setText(f"Total de leituras: {len(self.readings)} | Tempo: {elapsed_str}")
            
            # Update plots
            times = [r[0] for r in self.readings]
            visa_vals = [r[1] for r in self.readings]
            esp32_vals = [r[2] for r in self.readings]
            
            self.curve.setData(times, visa_vals)
            self.esp32_curve.setData(times, esp32_vals)
    
    # ----- Utility methods (same as single instrument) -----
    def format_number(self, value):
        """Format number for display (same as single instrument)"""
        if abs(value) >= 1000:
            return f"{value:.3e}"
        elif abs(value) >= 1:
            return f"{value:.3f}"
        else:
            return f"{value:.6e}"
    
    # ----- Save/Load parameters (same as single instrument) -----
    def save_parameters(self):
        """Save measurement parameters to JSON file"""
        params = {
            'voltage': self.voltage_spin.value(),
            'current_limit': self.ilim_spin.value(),
            'nplc': self.nplc_spin.value(),
            'interval': self.interval_spin.value()
        }
        
        default_dir = self._last_params_dir
        if not default_dir and self.user_manager:
            default_dir = str(self.user_manager.get_user_directory('parameters'))
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Parâmetros", default_dir or "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(params, f, indent=4)
                QMessageBox.information(self, "Sucesso", "Parâmetros salvos com sucesso!")
                self._last_params_dir = os.path.dirname(filename)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar parâmetros:\n{e}")
    
    def load_parameters(self):
        """Load measurement parameters from JSON file"""
        default_dir = self._last_params_dir
        if not default_dir and self.user_manager:
            default_dir = str(self.user_manager.get_user_directory('parameters'))
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Parâmetros", default_dir or "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    params = json.load(f)
                
                self.voltage_spin.setValue(params.get('voltage', 1.0))
                self.ilim_spin.setValue(params.get('current_limit', 1e-3))
                self.nplc_spin.setValue(params.get('nplc', 1.0))
                self.interval_spin.setValue(params.get('interval', 1.0))
                
                QMessageBox.information(self, "Sucesso", "Parâmetros carregados com sucesso!")
                self._last_params_dir = os.path.dirname(filename)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar parâmetros:\n{e}")
    
    # ----- Export/Load measurement (extends single instrument with ESP32 column) -----
    def export_measurement(self):
        """Export measurement data to text file"""
        if not self.readings:
            QMessageBox.warning(self, "Sem Dados", "Não há dados para exportar.")
            return
        
        default_dir = self._last_export_dir
        if not default_dir and self.user_manager:
            default_dir = str(self.user_manager.get_user_directory('exports'))
        
        default_filename = f"combined_measurement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        if default_dir:
            default_filename = os.path.join(default_dir, default_filename)
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar Medição", default_filename,
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    # Write metadata
                    f.write(f"# Medição Combinada - VISA + ESP32\n")
                    if self.user_manager:
                        user_info = self.user_manager.get_current_user_info()
                        f.write(f"# Usuário: {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n")
                    f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Tensão (V): {self.voltage_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
                    
                    esp32_unit = self.esp32_device.calibration.unit if self.esp32_device.calibration else "bits"
                    esp32_label = self.esp32_device.calibration.label if self.esp32_device.calibration else "ESP32"
                    
                    f.write(f"Tempo_(s)\tResistencia_(Ohms)\t{esp32_label}_({esp32_unit})\n")
                    
                    for t, res, esp32 in self.readings:
                        f.write(f"{t:.2f}\t{res:.6e}\t{esp32:.6f}\n")
                
                QMessageBox.information(self, "Sucesso", f"Medição exportada para:\n{filename}")
                self._last_export_dir = os.path.dirname(filename)
                self.logger.info(f"Measurement exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar:\n{e}")
    
    def load_measurement(self):
        """Load measurement data from file"""
        default_dir = self._last_load_dir
        if not default_dir and self.user_manager:
            default_dir = str(self.user_manager.get_user_directory('exports'))
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Medição", default_dir or "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                self.readings.clear()
                self.list_widget.clear()
                
                with open(filename, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if 'Tempo' in line:  # Skip header
                            continue
                        
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            t = float(parts[0])
                            res = float(parts[1])
                            esp32 = float(parts[2])
                            self.readings.append((t, res, esp32))
                
                # Update display
                if self.readings:
                    times = [r[0] for r in self.readings]
                    visa_vals = [r[1] for r in self.readings]
                    esp32_vals = [r[2] for r in self.readings]
                    
                    self.curve.setData(times, visa_vals)
                    self.esp32_curve.setData(times, esp32_vals)
                    
                    for t, res, esp32 in self.readings:
                        esp32_unit = self.esp32_device.calibration.unit if self.esp32_device.calibration else "bits"
                        self.list_widget.addItem(f"{t:.2f} s | {self.format_number(res)} Ω | ESP32: {esp32:.2f} {esp32_unit}")
                    
                    elapsed_str = str(timedelta(seconds=int(self.readings[-1][0])))
                    self.stats_label.setText(f"Total de leituras: {len(self.readings)} | Tempo: {elapsed_str}")
                
                QMessageBox.information(self, "Sucesso", f"Medição carregada:\n{len(self.readings)} pontos")
                self._last_load_dir = os.path.dirname(filename)
                self.logger.info(f"Measurement loaded from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar medição:\n{e}")
