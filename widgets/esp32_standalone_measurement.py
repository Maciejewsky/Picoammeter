"""
Standalone ESP32 Measurement Widget
For independent ESP32/ADS1115 measurements without VISA instrument
"""

import time
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QDoubleSpinBox, QSpinBox, QComboBox,
    QFileDialog, QMessageBox, QCheckBox, QFrame
)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
import pyqtgraph as pg
from pyqtgraph import PlotWidget, mkPen

from core.logger import get_logger


class ESP32StandaloneMeasurementWidget(QWidget):
    """Widget for standalone ESP32/ADS1115 measurements"""
    
    measurement_complete = pyqtSignal()
    
    def __init__(self, esp32_device, user_manager=None, parent=None):
        super().__init__(parent)
        
        self.esp32_device = esp32_device
        self.user_manager = user_manager
        self.logger = get_logger()
        
        # Measurement data
        self.time_data = []
        self.esp32_data = []
        
        # Measurement state
        self.measuring = False
        self.start_time = None
        
        # Timer for continuous measurements
        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self.perform_measurement)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Medição ESP32/ADS1115")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Device info
        info_layout = QHBoxLayout()
        device_label = QLabel(f"🔌 Dispositivo: {self.esp32_device.port}")
        device_label.setStyleSheet("font-size: 12px; color: #666666;")
        info_layout.addWidget(device_label)
        
        if self.esp32_device.calibration:
            calib_label = QLabel(
                f"📊 Canal: {self.esp32_device.calibration.channel} | "
                f"Tipo: {self.esp32_device.calibration.reading_type} | "
                f"Unidade: {self.esp32_device.calibration.unit}"
            )
            calib_label.setStyleSheet("font-size: 12px; color: #666666;")
            info_layout.addWidget(calib_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Parameters group
        params_group = QGroupBox("Parâmetros de Medição")
        params_layout = QVBoxLayout(params_group)
        
        # Measurement timing
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Intervalo (s):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setDecimals(1)
        timing_layout.addWidget(self.interval_spin)
        
        timing_layout.addWidget(QLabel("Duração Total (s):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 86400)
        self.duration_spin.setValue(60)
        timing_layout.addWidget(self.duration_spin)
        
        self.continuous_checkbox = QCheckBox("Medição Contínua")
        timing_layout.addWidget(self.continuous_checkbox)
        
        timing_layout.addStretch()
        params_layout.addLayout(timing_layout)
        
        layout.addWidget(params_group)
        
        # Plot widget
        self.setup_plot()
        layout.addWidget(self.plot_widget)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("Iniciar Medição")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_start.clicked.connect(self.start_measurement)
        control_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("Parar Medição")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_stop.clicked.connect(self.stop_measurement)
        control_layout.addWidget(self.btn_stop)
        
        self.btn_clear = QPushButton("Limpar Dados")
        self.btn_clear.clicked.connect(self.clear_data)
        control_layout.addWidget(self.btn_clear)
        
        self.btn_export = QPushButton("Exportar Dados")
        self.btn_export.clicked.connect(self.export_data)
        control_layout.addWidget(self.btn_export)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Aguardando início da medição...")
        self.status_label.setStyleSheet("padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        # Current value display
        self.esp32_value_label = QLabel("ESP32: ---")
        self.esp32_value_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
        status_layout.addWidget(self.esp32_value_label)
        
        layout.addWidget(status_group)
    
    def setup_plot(self):
        """Setup the plot widget"""
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('bottom', 'Tempo', units='s')
        
        # Set label based on calibration
        if self.esp32_device.calibration:
            label = self.esp32_device.calibration.label
            unit = self.esp32_device.calibration.unit
        else:
            label = "ADS1115"
            unit = "bits"
        
        self.plot_widget.setLabel('left', label, units=unit, color='#FF9800')
        self.plot_widget.getAxis('left').setPen('#FF9800')
        
        # Plot curve
        self.esp32_curve = self.plot_widget.plot(
            pen=mkPen(color='#FF9800', width=2),
            name='ESP32'
        )
        
        # Add legend
        self.plot_widget.addLegend()
    
    def start_measurement(self):
        """Start the measurement"""
        if self.measuring:
            return
        
        # Clear previous data
        self.clear_data()
        
        # Start measurement
        self.measuring = True
        self.start_time = time.time()
        
        # Update UI
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("Medição em andamento...")
        
        # Start timer
        interval_ms = int(self.interval_spin.value() * 1000)
        self.measurement_timer.start(interval_ms)
        
        self.logger.info("ESP32 standalone measurement started")
    
    def stop_measurement(self):
        """Stop the measurement"""
        if not self.measuring:
            return
        
        # Stop timer
        self.measurement_timer.stop()
        
        # Update state
        self.measuring = False
        
        # Update UI
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Medição parada.")
        
        self.logger.info("ESP32 standalone measurement stopped")
        self.measurement_complete.emit()
    
    def perform_measurement(self):
        """Perform a single measurement"""
        if not self.measuring:
            return
        
        # Calculate elapsed time
        elapsed_time = time.time() - self.start_time
        
        # Check if we should stop (duration reached)
        if not self.continuous_checkbox.isChecked():
            if elapsed_time >= self.duration_spin.value():
                self.stop_measurement()
                return
        
        try:
            # Read from ESP32/ADS1115
            esp32_reading = self.esp32_device.read_ads1115_calibrated()
            
            if esp32_reading is None:
                self.logger.warning("Failed to read from ESP32")
                esp32_reading = 0.0
            
            # Store data
            self.time_data.append(elapsed_time)
            self.esp32_data.append(esp32_reading)
            
            # Update plot
            self.esp32_curve.setData(self.time_data, self.esp32_data)
            
            # Update current value label
            if self.esp32_device.calibration:
                esp32_unit = self.esp32_device.calibration.unit
                if self.esp32_device.calibration.reading_type == "percentage":
                    self.esp32_value_label.setText(f"ESP32: {esp32_reading:.1f} {esp32_unit}")
                else:
                    self.esp32_value_label.setText(f"ESP32: {esp32_reading:.0f} {esp32_unit}")
            else:
                self.esp32_value_label.setText(f"ESP32: {esp32_reading:.0f}")
            
            # Update status
            num_points = len(self.time_data)
            self.status_label.setText(
                f"Medição em andamento... {num_points} pontos | Tempo: {elapsed_time:.1f} s"
            )
            
        except Exception as e:
            self.logger.error(f"Error during measurement: {e}")
            self.status_label.setText(f"Erro durante medição: {e}")
    
    def clear_data(self):
        """Clear all measurement data"""
        self.time_data = []
        self.esp32_data = []
        
        # Clear plot
        self.esp32_curve.setData([], [])
        
        # Clear value label
        self.esp32_value_label.setText("ESP32: ---")
        
        self.logger.info("Measurement data cleared")
    
    def export_data(self):
        """Export measurement data to TXT/CSV"""
        if not self.time_data:
            QMessageBox.warning(self, "Sem Dados", "Não há dados para exportar.")
            return
        
        # Get save filename
        default_filename = f"esp32_measurement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        if self.user_manager:
            export_dir = self.user_manager.get_user_directory('exports')
            default_path = f"{export_dir}/{default_filename}"
        else:
            default_path = default_filename
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Dados",
            default_path,
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            # Create header with metadata
            with open(filename, 'w') as f:
                # Write metadata
                f.write("# Keithley LabNano3D - Medição ESP32/ADS1115\n")
                
                if self.user_manager:
                    user_info = self.user_manager.get_current_user_info()
                    f.write(f"# Usuário: {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n")
                
                f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Dispositivo: {self.esp32_device.port}\n")
                f.write("#\n")
                f.write("# Parâmetros ESP32/ADS1115:\n")
                
                if self.esp32_device.calibration:
                    f.write(f"# Canal: {self.esp32_device.calibration.channel}\n")
                    f.write(f"# Tipo de Leitura: {self.esp32_device.calibration.reading_type}\n")
                    f.write(f"# Rótulo: {self.esp32_device.calibration.label}\n")
                    f.write(f"# Unidade: {self.esp32_device.calibration.unit}\n")
                    esp32_label = self.esp32_device.calibration.label
                    esp32_unit = self.esp32_device.calibration.unit
                else:
                    esp32_label = "ESP32"
                    esp32_unit = "bits"
                    
                f.write("#\n")
                f.write("# ---\n")
                
                # Write column headers
                f.write(f"Tempo (s)\t{esp32_label} ({esp32_unit})\n")
                
                # Write data
                for t, esp32_val in zip(self.time_data, self.esp32_data):
                    f.write(f"{t:.3f}\t{esp32_val:.6f}\n")
            
            QMessageBox.information(
                self, 
                "Exportação Concluída", 
                f"Dados exportados com sucesso para:\n{filename}"
            )
            
            self.logger.info(f"Data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar dados:\n{e}")
