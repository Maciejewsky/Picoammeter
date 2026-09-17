"""
Connection window v2 for Keithley LabNano3D
Supports both real and simulated instruments with modern interface
"""

import sys
import pyvisa
import threading
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QMessageBox, QTabWidget, QWidget, QGroupBox, QCheckBox, QComboBox,
    QTextEdit, QProgressBar, QFrame
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt, QTimer
from PyQt5.QtGui import QFont

from core.debug_mode import get_debug_manager
from core.logger import get_logger


class WorkerSignals(QObject):
    """Signals for instrument scanning thread"""
    device_found = pyqtSignal(dict)  # device_info dict
    scan_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)


class InstrumentScanThread(threading.Thread):
    """Thread for scanning real VISA instruments"""
    
    def __init__(self, rm, signals):
        super().__init__()
        self.rm = rm
        self.signals = signals
        self._stop_event = threading.Event()
    
    def run(self):
        """Run the instrument scan"""
        try:
            resources = self.rm.list_resources()
        except Exception as e:
            self.signals.error_occurred.emit(f"Erro ao listar recursos VISA: {e}")
            self.signals.scan_finished.emit()
            return
        
        if not resources:
            self.signals.scan_finished.emit()
            return
        
        for resource in resources:
            if self._stop_event.is_set():
                break
            
            try:
                inst = self.rm.open_resource(resource, timeout=1000)
                inst.write_termination = "\r"
                inst.read_termination = "\r"
                
                idn = inst.query("*IDN?").strip()
                inst.close()
                
                # Parse IDN response
                device_info = self._parse_idn_response(idn, resource)
                self.signals.device_found.emit(device_info)
                
            except Exception as e:
                # Add device with error status
                device_info = {
                    "name": f"Device at {resource}",
                    "model": "Unknown",
                    "address": resource,
                    "idn": None,
                    "status": f"Error: {e}",
                    "type": "real"
                }
                self.signals.device_found.emit(device_info)
        
        self.signals.scan_finished.emit()
    
    def _parse_idn_response(self, idn, address):
        """Parse IDN response and create device info"""
        parts = idn.split(',')
        manufacturer = parts[0].strip() if len(parts) > 0 else "Unknown"
        model = parts[1].strip() if len(parts) > 1 else "Unknown"
        serial = parts[2].strip() if len(parts) > 2 else "Unknown"
        
        # Determine device type and name
        model_upper = model.upper()
        if "2450" in model_upper:
            device_name = f"SMU 2450 ({serial})"
            device_type = "smu_2450"
        elif "6487" in model_upper:
            device_name = f"Picoamperímetro 6487 ({serial})"
            device_type = "pico_6487"
        else:
            device_name = f"{model} ({serial})"
            device_type = "unknown"
        
        return {
            "name": device_name,
            "model": model,
            "manufacturer": manufacturer,
            "serial": serial,
            "address": address,
            "idn": idn,
            "status": "Available",
            "type": "real",
            "device_type": device_type
        }
    
    def stop(self):
        """Stop the scanning thread"""
        self._stop_event.set()


class RealInstrumentsTab(QWidget):
    """Tab for real VISA instruments"""
    
    instrument_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rm = None
        self.scan_thread = None
        self.signals = WorkerSignals()
        self.available_devices = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Initialize VISA resource manager
        self.init_visa()
    
    def setup_ui(self):
        """Setup the UI for real instruments tab"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Conecte seus instrumentos Keithley via USB ou Ethernet e clique em 'Buscar Instrumentos'."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Scan controls
        scan_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Buscar Instrumentos")
        self.btn_scan.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.btn_scan)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        scan_layout.addWidget(self.progress_bar)
        
        scan_layout.addStretch()
        layout.addLayout(scan_layout)
        
        # Devices list
        self.devices_list = QListWidget()
        self.devices_list.itemDoubleClicked.connect(self.on_device_double_click)
        layout.addWidget(self.devices_list)
        
        # Status label
        self.status_label = QLabel("Clique em 'Buscar Instrumentos' para procurar dispositivos.")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Connect button
        self.btn_connect = QPushButton("Conectar Selecionado")
        self.btn_connect.setEnabled(False)
        self.btn_connect.clicked.connect(self.connect_selected)
        layout.addWidget(self.btn_connect)
    
    def connect_signals(self):
        """Connect internal signals"""
        self.signals.device_found.connect(self.add_device)
        self.signals.scan_finished.connect(self.scan_finished)
        self.signals.error_occurred.connect(self.show_error)
        
        self.devices_list.itemSelectionChanged.connect(self.on_selection_changed)
    
    def init_visa(self):
        """Initialize VISA resource manager"""
        try:
            self.rm = pyvisa.ResourceManager()
            self.status_label.setText("VISA inicializado. Pronto para buscar instrumentos.")
        except Exception as e:
            self.status_label.setText(f"Erro ao inicializar VISA: {e}")
            self.btn_scan.setEnabled(False)
    
    def start_scan(self):
        """Start scanning for instruments"""
        if not self.rm:
            return
        
        if self.scan_thread and self.scan_thread.is_alive():
            return
        
        # Clear previous results
        self.devices_list.clear()
        self.available_devices.clear()
        self.btn_connect.setEnabled(False)
        
        # Update UI
        self.btn_scan.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Procurando instrumentos...")
        
        # Start scan thread
        self.scan_thread = InstrumentScanThread(self.rm, self.signals)
        self.scan_thread.start()
    
    def add_device(self, device_info):
        """Add found device to list"""
        self.available_devices.append(device_info)
        
        # Create display text
        display_text = f"{device_info['name']} - {device_info['status']}"
        if device_info['status'].startswith('Error'):
            display_text += f" ({device_info['address']})"
        
        self.devices_list.addItem(display_text)
    
    def scan_finished(self):
        """Handle scan completion"""
        self.btn_scan.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        count = len(self.available_devices)
        if count == 0:
            self.status_label.setText("Nenhum instrumento VISA encontrado.")
        else:
            self.status_label.setText(f"{count} instrumento(s) encontrado(s).")
    
    def show_error(self, error_message):
        """Show error message"""
        QMessageBox.warning(self, "Erro", error_message)
        self.status_label.setText(f"Erro: {error_message}")
    
    def on_selection_changed(self):
        """Handle device selection change"""
        selected_items = self.devices_list.selectedItems()
        if selected_items:
            index = self.devices_list.row(selected_items[0])
            if 0 <= index < len(self.available_devices):
                device = self.available_devices[index]
                self.btn_connect.setEnabled(device['status'] == 'Available')
        else:
            self.btn_connect.setEnabled(False)
    
    def on_device_double_click(self, item):
        """Handle device double-click"""
        self.connect_selected()
    
    def connect_selected(self):
        """Connect to selected device"""
        selected_items = self.devices_list.selectedItems()
        if not selected_items:
            return
        
        index = self.devices_list.row(selected_items[0])
        if not (0 <= index < len(self.available_devices)):
            return
        
        device_info = self.available_devices[index]
        
        if device_info['status'] != 'Available':
            QMessageBox.warning(self, "Dispositivo Indisponível", 
                              "Este dispositivo não está disponível para conexão.")
            return
        
        try:
            # Open connection
            instrument = self.rm.open_resource(device_info['address'], timeout=5000)
            instrument.read_termination = "\r"
            instrument.write_termination = "\n"
            
            # Test communication
            idn = instrument.query("*IDN?").strip()
            
            # Add instrument object to device info
            device_info['instrument'] = instrument
            
            # Emit signal
            self.instrument_selected.emit(device_info)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", 
                               f"Não foi possível conectar ao dispositivo:\n{e}")


class SimulatedInstrumentsTab(QWidget):
    """Tab for simulated instruments (debug mode)"""
    
    instrument_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug_manager = get_debug_manager()
        self.setup_ui()
        self.load_simulated_instruments()
    
    def setup_ui(self):
        """Setup the UI for simulated instruments tab"""
        layout = QVBoxLayout(self)
        
        # Debug mode notice
        notice = QLabel("🔧 MODO DEBUG - Instrumentos Simulados")
        notice.setStyleSheet("""
            background-color: #FF9800;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
        """)
        notice.setAlignment(Qt.AlignCenter)
        layout.addWidget(notice)
        
        # Instructions
        instructions = QLabel(
            "Selecione um instrumento simulado para teste e desenvolvimento. "
            "Estes instrumentos geram dados sintéticos para fins de demonstração."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Instruments list
        self.sim_devices_list = QListWidget()
        self.sim_devices_list.itemDoubleClicked.connect(self.connect_selected)
        layout.addWidget(self.sim_devices_list)
        
        # Add custom instrument section
        custom_group = QGroupBox("Adicionar Instrumento Personalizado")
        custom_layout = QHBoxLayout(custom_group)
        
        custom_layout.addWidget(QLabel("Tipo:"))
        self.instrument_type_combo = QComboBox()
        self.instrument_type_combo.addItems(["SMU2450", "PICO6487"])
        custom_layout.addWidget(self.instrument_type_combo)
        
        self.btn_add_custom = QPushButton("Adicionar")
        self.btn_add_custom.clicked.connect(self.add_custom_instrument)
        custom_layout.addWidget(self.btn_add_custom)
        
        layout.addWidget(custom_group)
        
        # Connect button
        self.btn_connect_sim = QPushButton("Conectar Simulado")
        self.btn_connect_sim.setEnabled(False)
        self.btn_connect_sim.clicked.connect(self.connect_selected)
        layout.addWidget(self.btn_connect_sim)
        
        # Enable connect button when selection changes
        self.sim_devices_list.itemSelectionChanged.connect(
            lambda: self.btn_connect_sim.setEnabled(
                len(self.sim_devices_list.selectedItems()) > 0
            )
        )
    
    def load_simulated_instruments(self):
        """Load available simulated instruments"""
        instruments = self.debug_manager.list_available_instruments()
        
        for instrument in instruments:
            display_text = f"{instrument['name']} ({instrument['model']})"
            if instrument['connected']:
                display_text += " - Conectado"
            
            self.sim_devices_list.addItem(display_text)
    
    def add_custom_instrument(self):
        """Add custom simulated instrument"""
        instrument_type = self.instrument_type_combo.currentText()
        
        try:
            # Generate unique name
            count = self.sim_devices_list.count()
            name = f"CUSTOM_{instrument_type}_{count + 1}"
            
            # Add to debug manager
            self.debug_manager.add_custom_instrument(name, instrument_type)
            
            # Add to list
            display_text = f"{name} (MODEL {instrument_type})"
            self.sim_devices_list.addItem(display_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao adicionar instrumento: {e}")
    
    def connect_selected(self):
        """Connect to selected simulated instrument"""
        selected_items = self.sim_devices_list.selectedItems()
        if not selected_items:
            return
        
        # Get selected instrument name
        selected_text = selected_items[0].text()
        # Extract instrument name (before the first space or parenthesis)
        instrument_name = selected_text.split(' ')[0]
        if instrument_name.startswith('CUSTOM_'):
            # For custom instruments, get the full name before the parenthesis
            instrument_name = selected_text.split(' (')[0]
        
        # Get instrument from debug manager
        instrument = self.debug_manager.get_instrument(instrument_name)
        if not instrument:
            QMessageBox.warning(self, "Erro", "Instrumento simulado não encontrado.")
            return
        
        try:
            # Connect the simulated instrument
            instrument.connect()
            
            # Create device info
            device_info = {
                "name": instrument_name,
                "model": instrument.model,
                "manufacturer": "KEITHLEY INSTRUMENTS (Simulated)",
                "serial": instrument.serial,
                "address": instrument.address,
                "idn": f"KEITHLEY INSTRUMENTS,{instrument.model},{instrument.serial},SIM.1.0",
                "status": "Connected (Simulated)",
                "type": "simulated",
                "device_type": "smu_2450" if "2450" in instrument.model else "pico_6487",
                "instrument": instrument
            }
            
            # Emit signal
            self.instrument_selected.emit(device_info)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", 
                               f"Erro ao conectar instrumento simulado:\n{e}")


class ConnectionWindowV2(QDialog):
    """Connection window v2 with support for real and simulated instruments"""
    
    instrument_connected = pyqtSignal(dict)
    
    def __init__(self, debug_mode=False, parent=None):
        super().__init__(parent)
        self.debug_mode = debug_mode
        self.logger = get_logger()
        
        self.setWindowTitle("Conectar Instrumentos - LabNano3D v2.0")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.logger.info("Connection window v2 opened")
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Conectar Instrumentos")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tabs for different connection types
        self.tabs = QTabWidget()
        
        # Real instruments tab
        self.real_tab = RealInstrumentsTab()
        self.real_tab.instrument_selected.connect(self.on_instrument_connected)
        self.tabs.addTab(self.real_tab, "Instrumentos Reais")
        
        # Simulated instruments tab (only in debug mode)
        if self.debug_mode:
            self.sim_tab = SimulatedInstrumentsTab()
            self.sim_tab.instrument_selected.connect(self.on_instrument_connected)
            self.tabs.addTab(self.sim_tab, "Instrumentos Simulados")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_close)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def on_instrument_connected(self, device_info):
        """Handle successful instrument connection"""
        # Show success message
        QMessageBox.information(
            self, "Conexão Bem-sucedida", 
            f"Conectado com sucesso a:\n{device_info['name']}\n\n"
            f"Modelo: {device_info['model']}\n"
            f"Endereço: {device_info['address']}"
        )
        
        # Emit signal and close dialog
        self.instrument_connected.emit(device_info)
        self.logger.info(f"Instrument connected: {device_info['name']} ({device_info['type']})")
        
        # Don't close the dialog, allow multiple connections
        # self.accept()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = ConnectionWindowV2(debug_mode=True)
    window.show()
    sys.exit(app.exec_())