"""
ESP32 Connection Widget for Keithley LabNano3D
Widget for connecting to ESP32 devices and configuring ADS1115
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QDoubleSpinBox,
    QRadioButton, QButtonGroup, QFrame, QProgressBar
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont

from core.esp32_manager import (
    get_esp32_manager, ESP32Device, ADS1115Calibration, 
    ADS1115Channel, ADS1115Gain
)
from core.logger import get_logger


class ADS1115CalibrationDialog(QWidget):
    """Dialog for calibrating ADS1115 readings"""
    
    calibration_updated = pyqtSignal(object)  # Emits ADS1115Calibration
    
    def __init__(self, device: ESP32Device = None, parent=None):
        super().__init__(parent)
        self.device = device
        self.logger = get_logger()
        self.current_calibration = ADS1115Calibration()
        
        if device and device.calibration:
            self.current_calibration = device.calibration
        
        self.setup_ui()
        self.update_from_calibration()
    
    def setup_ui(self):
        """Setup the calibration UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Calibração ADS1115")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Channel selection
        channel_group = QGroupBox("Canal")
        channel_layout = QVBoxLayout(channel_group)
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItem("A0 (Single-ended)", ADS1115Channel.A0)
        self.channel_combo.addItem("A1 (Single-ended)", ADS1115Channel.A1)
        self.channel_combo.addItem("A2 (Single-ended)", ADS1115Channel.A2)
        self.channel_combo.addItem("A3 (Single-ended)", ADS1115Channel.A3)
        self.channel_combo.addItem("A0-A1 (Differential)", ADS1115Channel.A0_A1)
        self.channel_combo.addItem("A0-A3 (Differential)", ADS1115Channel.A0_A3)
        self.channel_combo.addItem("A2-A3 (Differential)", ADS1115Channel.A2_A3)
        self.channel_combo.addItem("A1-A3 (Differential)", ADS1115Channel.A1_A3)
        channel_layout.addWidget(self.channel_combo)
        
        layout.addWidget(channel_group)
        
        # Reading type selection
        type_group = QGroupBox("Tipo de Leitura")
        type_layout = QVBoxLayout(type_group)
        
        self.reading_type_group = QButtonGroup(self)
        
        self.radio_raw = QRadioButton("Leitura Bruta (bits)")
        self.radio_raw.setChecked(True)
        self.reading_type_group.addButton(self.radio_raw, 0)
        type_layout.addWidget(self.radio_raw)
        
        self.radio_percentage = QRadioButton("Percentual (0-100%)")
        self.reading_type_group.addButton(self.radio_percentage, 1)
        type_layout.addWidget(self.radio_percentage)
        
        # Connect signal
        self.reading_type_group.buttonClicked.connect(self.on_reading_type_changed)
        
        layout.addWidget(type_group)
        
        # Custom label and unit
        label_group = QGroupBox("Identificação")
        label_layout = QVBoxLayout(label_group)
        
        label_h = QHBoxLayout()
        label_h.addWidget(QLabel("Rótulo:"))
        self.label_edit = QLineEdit("ADS1115")
        label_h.addWidget(self.label_edit)
        label_layout.addLayout(label_h)
        
        unit_h = QHBoxLayout()
        unit_h.addWidget(QLabel("Unidade:"))
        self.unit_edit = QLineEdit("bits")
        unit_h.addWidget(self.unit_edit)
        label_layout.addLayout(unit_h)
        
        layout.addWidget(label_group)
        
        # Calibration values
        calib_group = QGroupBox("Calibração")
        calib_layout = QVBoxLayout(calib_group)
        
        # Min value
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Valor Mínimo:"))
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(-32768, 32767)
        self.min_spinbox.setValue(0)
        self.min_spinbox.setDecimals(0)
        min_layout.addWidget(self.min_spinbox)
        calib_layout.addLayout(min_layout)
        
        # Max value
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Valor Máximo:"))
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(-32768, 32767)
        self.max_spinbox.setValue(32767)
        self.max_spinbox.setDecimals(0)
        max_layout.addWidget(self.max_spinbox)
        calib_layout.addLayout(max_layout)
        
        # Current reading display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Leitura Atual:"))
        self.current_reading_label = QLabel("---")
        self.current_reading_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        current_layout.addWidget(self.current_reading_label)
        current_layout.addStretch()
        
        # Buttons to set min/max from current reading
        self.btn_set_min = QPushButton("Definir como Mín")
        self.btn_set_min.clicked.connect(self.set_current_as_min)
        current_layout.addWidget(self.btn_set_min)
        
        self.btn_set_max = QPushButton("Definir como Máx")
        self.btn_set_max.clicked.connect(self.set_current_as_max)
        current_layout.addWidget(self.btn_set_max)
        
        calib_layout.addLayout(current_layout)
        
        # Auto-update toggle
        auto_update_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Atualizar Leitura")
        self.btn_refresh.clicked.connect(self.refresh_current_reading)
        auto_update_layout.addWidget(self.btn_refresh)
        auto_update_layout.addStretch()
        calib_layout.addLayout(auto_update_layout)
        
        layout.addWidget(calib_group)
        
        # Inverted warning
        self.inversion_label = QLabel("⚠️ Leitura invertida detectada")
        self.inversion_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.inversion_label.setVisible(False)
        layout.addWidget(self.inversion_label)
        
        # Apply button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_apply = QPushButton("Aplicar Calibração")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_apply.clicked.connect(self.apply_calibration)
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
        # Timer for auto-refresh (optional)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_current_reading)
    
    def on_reading_type_changed(self):
        """Handle reading type change"""
        if self.radio_percentage.isChecked():
            self.unit_edit.setText("%")
        else:
            self.unit_edit.setText("bits")
    
    def update_from_calibration(self):
        """Update UI from current calibration"""
        # Set channel
        index = self.channel_combo.findData(self.current_calibration.channel)
        if index >= 0:
            self.channel_combo.setCurrentIndex(index)
        
        # Set reading type
        if self.current_calibration.reading_type == "percentage":
            self.radio_percentage.setChecked(True)
        else:
            self.radio_raw.setChecked(True)
        
        # Set label and unit
        self.label_edit.setText(self.current_calibration.label)
        self.unit_edit.setText(self.current_calibration.unit)
        
        # Set min/max
        self.min_spinbox.setValue(self.current_calibration.raw_min)
        self.max_spinbox.setValue(self.current_calibration.raw_max)
    
    def refresh_current_reading(self):
        """Refresh the current reading from device"""
        if not self.device or not self.device.connected:
            self.current_reading_label.setText("Não conectado")
            return
        
        try:
            channel = self.channel_combo.currentData()
            raw_value = self.device.read_ads1115(channel=channel)
            
            if raw_value is not None:
                self.current_reading_label.setText(f"{raw_value:.0f}")
            else:
                self.current_reading_label.setText("Erro na leitura")
                
        except Exception as e:
            self.logger.error(f"Error refreshing reading: {e}")
            self.current_reading_label.setText("Erro")
    
    def set_current_as_min(self):
        """Set current reading as minimum value"""
        try:
            value_text = self.current_reading_label.text()
            if value_text and value_text not in ["---", "Não conectado", "Erro", "Erro na leitura"]:
                value = float(value_text)
                self.min_spinbox.setValue(value)
        except ValueError:
            pass
    
    def set_current_as_max(self):
        """Set current reading as maximum value"""
        try:
            value_text = self.current_reading_label.text()
            if value_text and value_text not in ["---", "Não conectado", "Erro", "Erro na leitura"]:
                value = float(value_text)
                self.max_spinbox.setValue(value)
        except ValueError:
            pass
    
    def apply_calibration(self):
        """Apply the calibration settings"""
        # Create new calibration
        calibration = ADS1115Calibration()
        
        # Set channel
        calibration.channel = self.channel_combo.currentData()
        
        # Set reading type
        if self.radio_percentage.isChecked():
            calibration.reading_type = "percentage"
        else:
            calibration.reading_type = "raw"
        
        # Set label and unit
        calibration.label = self.label_edit.text()
        calibration.unit = self.unit_edit.text()
        
        # Set calibration values
        min_val = self.min_spinbox.value()
        max_val = self.max_spinbox.value()
        calibration.calibrate(min_val, max_val)
        
        # Show inversion warning if needed
        self.inversion_label.setVisible(calibration.inverted)
        
        # Update device
        if self.device:
            self.device.set_calibration(calibration)
        
        # Emit signal
        self.calibration_updated.emit(calibration)
        
        QMessageBox.information(self, "Calibração Aplicada", 
                              "A calibração foi aplicada com sucesso!")


class ESP32ConnectionWidget(QWidget):
    """Widget for connecting to ESP32 devices"""
    
    esp32_connected = pyqtSignal(object)  # Emits ESP32Device
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = get_esp32_manager()
        self.logger = get_logger()
        self.connected_device = None
        self.calibration_dialog = None  # Reuse dialog instance
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the ESP32 connection UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Conecte seu ESP32 via USB e clique em 'Buscar Dispositivos'."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scan controls
        scan_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Buscar Dispositivos")
        self.btn_scan.clicked.connect(self.scan_devices)
        scan_layout.addWidget(self.btn_scan)
        scan_layout.addStretch()
        layout.addLayout(scan_layout)
        
        # Devices list
        self.devices_list = QListWidget()
        self.devices_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.devices_list)
        
        # Status label
        self.status_label = QLabel("Clique em 'Buscar Dispositivos' para procurar ESP32.")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Connection controls
        button_layout = QHBoxLayout()
        
        self.btn_connect = QPushButton("Conectar Selecionado")
        self.btn_connect.setEnabled(False)
        self.btn_connect.clicked.connect(self.connect_selected)
        button_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self.disconnect_device)
        button_layout.addWidget(self.btn_disconnect)
        
        layout.addLayout(button_layout)
        
        # Calibration button
        self.btn_calibrate = QPushButton("⚙️ Calibrar ADS1115")
        self.btn_calibrate.setEnabled(False)
        self.btn_calibrate.clicked.connect(self.open_calibration)
        layout.addWidget(self.btn_calibrate)
    
    def scan_devices(self):
        """Scan for available ESP32 devices"""
        self.devices_list.clear()
        self.status_label.setText("Procurando dispositivos...")
        
        try:
            ports = self.manager.list_available_ports()
            
            if not ports:
                self.status_label.setText("Nenhuma porta serial encontrada.")
                return
            
            for port_info in ports:
                display_text = f"{port_info['port']} - {port_info['description']}"
                self.devices_list.addItem(display_text)
            
            self.status_label.setText(f"{len(ports)} porta(s) encontrada(s).")
            
        except Exception as e:
            self.logger.error(f"Error scanning devices: {e}")
            self.status_label.setText(f"Erro ao procurar dispositivos: {e}")
    
    def on_selection_changed(self):
        """Handle device selection change"""
        selected_items = self.devices_list.selectedItems()
        self.btn_connect.setEnabled(len(selected_items) > 0 and not self.connected_device)
    
    def connect_selected(self):
        """Connect to selected ESP32 device"""
        selected_items = self.devices_list.selectedItems()
        if not selected_items:
            return
        
        # Extract port from display text
        selected_text = selected_items[0].text()
        port = selected_text.split(' - ')[0]
        
        try:
            # Connect to device
            device = self.manager.connect_device(port)
            
            if device:
                self.connected_device = device
                self.btn_connect.setEnabled(False)
                self.btn_disconnect.setEnabled(True)
                self.btn_calibrate.setEnabled(True)
                self.status_label.setText(f"Conectado a {port}")
                
                # Emit signal
                self.esp32_connected.emit(device)
                
                QMessageBox.information(self, "Conexão Bem-sucedida",
                                      f"Conectado ao ESP32 em {port}")
            else:
                QMessageBox.warning(self, "Erro de Conexão",
                                  "Não foi possível conectar ao ESP32.")
                
        except Exception as e:
            self.logger.error(f"Error connecting to ESP32: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao conectar: {e}")
    
    def disconnect_device(self):
        """Disconnect from ESP32 device"""
        if not self.connected_device:
            return
        
        try:
            port = self.connected_device.port
            self.manager.disconnect_device(port)
            
            self.connected_device = None
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_calibrate.setEnabled(False)
            self.status_label.setText("Desconectado")
            
            QMessageBox.information(self, "Desconectado",
                                  f"Desconectado do ESP32 em {port}")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting ESP32: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao desconectar: {e}")
    
    def open_calibration(self):
        """Open calibration dialog"""
        if not self.connected_device:
            QMessageBox.warning(self, "Não Conectado",
                              "Conecte-se a um ESP32 antes de calibrar.")
            return
        
        # Reuse existing dialog or create new one
        if self.calibration_dialog is None:
            self.calibration_dialog = ADS1115CalibrationDialog(self.connected_device)
            self.calibration_dialog.setWindowTitle("Calibração ADS1115")
            self.calibration_dialog.setMinimumSize(400, 500)
        else:
            # Update device reference if needed
            self.calibration_dialog.device = self.connected_device
            self.calibration_dialog.update_from_calibration()
        
        self.calibration_dialog.show()
        self.calibration_dialog.raise_()
        self.calibration_dialog.activateWindow()
