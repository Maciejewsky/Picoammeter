"""
Main application window for Keithley LabNano3D v2.0
Modern interface with inactive start state and multi-instrument support
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QFrame, QMessageBox, QApplication, QMenuBar,
    QMenu, QAction, QStatusBar, QSplitter, QGroupBox, QGridLayout,
    QTextEdit, QListWidget, QFileDialog, QComboBox, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QProgressBar, QToolButton, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPalette

from core.logger import get_logger
from core.debug_mode import get_debug_manager
from connection_window_v2 import ConnectionWindowV2, RealInstrumentsTab, SimulatedInstrumentsTab, WorkerSignals, InstrumentScanThread
from widgets.smu_2450.main_2450 import SMU2450Widget
from widgets.smu_2450.block_resistance_time import ResistanceMeasurementBlock
from widgets.smu_2450.block_iv_measurement import IVMeasurementBlock
from widgets.pico_6487.main_6487 import Pico6487Widget
from widgets.pico_6487.block_resistance_time import ResistanceMeasurementBlock as Pico6487ResistanceBlock
from widgets.pico_6487.block_iv_measurement import IVMeasurementBlock as Pico6487IVBlock
from widgets.pico_6487.block_charge_discharge import ChargeDischargeBlock as Pico6487ChargeDischargeBlock
from widgets.pico_6487.block_source_control import SourceControlBlock as Pico6487SourceControlBlock
from widgets.script_editor_widget import ScriptEditorWidget


class CollapsibleSidebar(QWidget):
    """A collapsible sidebar widget that can be toggled"""

    def __init__(self, title="Sidebar", parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.setup_ui(title)

    def setup_ui(self, title):
        """Setup the collapsible sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with toggle button
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #37474F;
                border-bottom: 1px solid #263238;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)

        # Toggle button
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("◀")  # Left arrow when expanded
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        header_layout.addWidget(self.toggle_btn)

        layout.addWidget(header)

        # Content container
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.content_container)

    def add_widget(self, widget):
        """Add a widget to the sidebar content"""
        self.content_layout.addWidget(widget)

    def add_stretch(self):
        """Add stretch to the content layout"""
        self.content_layout.addStretch()

    def toggle(self):
        """Toggle the sidebar collapsed state"""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.content_container.hide()
            self.toggle_btn.setText("▶")  # Right arrow when collapsed
            self.setMaximumWidth(150)
        else:
            self.content_container.show()
            self.toggle_btn.setText("◀")  # Left arrow when expanded
            self.setMaximumWidth(400)
            self.setMinimumWidth(300)


class SourceStatusWidget(QWidget):
    """Widget to display source status (ON/OFF, voltage, current)"""

    source_toggled = pyqtSignal(bool)  # Emits True for ON, False for OFF

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_on = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the source status UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Status indicator
        self.status_label = QLabel("Fonte: DESLIGADA")
        self.status_label.setStyleSheet("""
            background-color: #f44336;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_label)

        # Voltage display
        self.voltage_label = QLabel("V: 0.000 V")
        layout.addWidget(self.voltage_label)

        # Current display
        self.current_label = QLabel("I: 0.000 A")
        layout.addWidget(self.current_label)

        layout.addStretch()

        # Toggle button
        self.btn_toggle = QPushButton("Ligar Fonte")
        self.btn_toggle.setMaximumWidth(120)
        self.btn_toggle.clicked.connect(self.toggle_source)
        layout.addWidget(self.btn_toggle)

    def toggle_source(self):
        """Toggle source on/off"""
        self.source_on = not self.source_on
        self.update_status()
        self.source_toggled.emit(self.source_on)

    def update_status(self):
        """Update the status display"""
        if self.source_on:
            self.status_label.setText("Fonte: LIGADA")
            self.status_label.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            """)
            self.btn_toggle.setText("Desligar Fonte")
        else:
            self.status_label.setText("Fonte: DESLIGADA")
            self.status_label.setStyleSheet("""
                background-color: #f44336;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            """)
            self.btn_toggle.setText("Ligar Fonte")

    def update_values(self, voltage, current):
        """Update voltage and current display"""
        self.voltage_label.setText(f"V: {voltage:.3f} V")
        self.current_label.setText(f"I: {current:.6f} A")


class MeasurementControlWidget(QWidget):
    """Widget to control which measurement is displayed"""

    measurement_changed = pyqtSignal(str)  # Emits measurement type: "resistance", "iv", "current"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the measurement control UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Label
        layout.addWidget(QLabel("Tipo de Medição:"))

        # Measurement selector
        self.measurement_selector = QComboBox()
        self.measurement_selector.addItem("Resistência", "resistance")
        self.measurement_selector.addItem("Curva I-V", "iv")
        self.measurement_selector.addItem("Carga / Descarga", "charge_discharge")
        self.measurement_selector.addItem("Voltametria Cíclica", "cyclic_voltammetry")
        self.measurement_selector.addItem("Fonte", "source")
        self.measurement_selector.currentIndexChanged.connect(self.on_selection_changed)
        layout.addWidget(self.measurement_selector)

        layout.addStretch()

    def on_selection_changed(self):
        """Handle measurement type selection change"""
        measurement_type = self.measurement_selector.currentData()
        if measurement_type:
            self.measurement_changed.emit(measurement_type)


class InstrumentManagementWidget(QWidget):
    """Widget for managing instrument connections (embedded in main window)"""

    instrument_connected = pyqtSignal(dict)
    esp32_connected = pyqtSignal(object)  # Emits ESP32Device

    def __init__(self, debug_mode=False, show_esp32=False, parent=None):
        super().__init__(parent)
        self.debug_mode = debug_mode
        self.show_esp32 = show_esp32
        self.setup_ui()

    def setup_ui(self):
        """Setup the instrument management UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Gerenciamento de Instrumentos")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Tab widget for real vs simulated
        self.tabs = QTabWidget()

        # Real instruments tab
        self.real_tab = RealInstrumentsTab()
        self.real_tab.instrument_selected.connect(self.on_instrument_selected)
        self.tabs.addTab(self.real_tab, "Instrumentos Reais")

        # Simulated instruments tab (if debug mode)
        if self.debug_mode:
            self.sim_tab = SimulatedInstrumentsTab()
            self.sim_tab.instrument_selected.connect(self.on_instrument_selected)
            self.tabs.addTab(self.sim_tab, "Instrumentos Simulados")

        # ESP32 tab (if show_esp32 enabled)
        if self.show_esp32:
            from widgets.esp32_connection_widget import ESP32ConnectionWidget
            self.esp32_tab = ESP32ConnectionWidget()
            self.esp32_tab.esp32_connected.connect(self.on_esp32_connected)
            self.tabs.addTab(self.esp32_tab, "ESP32")

        layout.addWidget(self.tabs)

    def on_instrument_selected(self, device_info):
        """Handle instrument selection"""
        self.instrument_connected.emit(device_info)

    def on_esp32_connected(self, device):
        """Handle ESP32 connection"""
        self.esp32_connected.emit(device)

    def enable_esp32_tab(self):
        """Enable ESP32 tab dynamically"""
        if not self.show_esp32:
            self.show_esp32 = True
            from widgets.esp32_connection_widget import ESP32ConnectionWidget
            self.esp32_tab = ESP32ConnectionWidget()
            self.esp32_tab.esp32_connected.connect(self.on_esp32_connected)
            self.tabs.addTab(self.esp32_tab, "ESP32")


class ModeSelectionWidget(QWidget):
    """Widget for selecting operation mode after login"""

    mode_selected = pyqtSignal(str)  # Emits mode: "new_measurement", "load_data"

    def __init__(self, user_name="", parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.setup_ui()

    def setup_ui(self):
        """Setup the mode selection UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        # Welcome message with username
        welcome_label = QLabel(f"Bem-vindo, {self.user_name}!")
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Instructions
        instruction_label = QLabel("Selecione o modo de operação:")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size: 16px; color: #666666;")
        layout.addWidget(instruction_label)

        layout.addSpacing(20)

        # Mode buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        # New measurement mode
        self.btn_new_measurement = QPushButton("Nova Medição")
        self.btn_new_measurement.setMinimumSize(250, 150)
        self.btn_new_measurement.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.btn_new_measurement.clicked.connect(lambda: self.mode_selected.emit("new_measurement"))
        button_layout.addWidget(self.btn_new_measurement)

        # Load data mode
        self.btn_load = QPushButton("Carregar Dados")
        self.btn_load.setMinimumSize(250, 150)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.btn_load.clicked.connect(lambda: self.mode_selected.emit("load_data"))
        button_layout.addWidget(self.btn_load)

        layout.addLayout(button_layout)


class InstrumentStatusWidget(QWidget):
    """Widget to display status of connected instruments and select active one"""

    active_instrument_changed = pyqtSignal(str)  # Emits instrument name when selection changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.instruments = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for instrument status"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Instrumentos Conectados")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Active instrument selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Instrumento Ativo:"))
        self.instrument_selector = QComboBox()
        self.instrument_selector.addItem("Nenhum")
        self.instrument_selector.currentTextChanged.connect(self.on_selection_changed)
        selector_layout.addWidget(self.instrument_selector)
        layout.addLayout(selector_layout)

        # Instruments list
        self.instruments_list = QListWidget()
        self.instruments_list.setMaximumHeight(120)
        layout.addWidget(self.instruments_list)

        # Status label
        self.status_label = QLabel("Nenhum instrumento conectado")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.status_label)

    def add_instrument(self, name, model, address):
        """Add instrument to status display"""
        self.instruments[name] = {"model": model, "address": address}
        self.update_display()

    def remove_instrument(self, name):
        """Remove instrument from status display"""
        if name in self.instruments:
            del self.instruments[name]
            self.update_display()

    def update_display(self):
        """Update the instruments display"""
        self.instruments_list.clear()

        # Update selector
        current_selection = self.instrument_selector.currentText()
        self.instrument_selector.clear()

        if not self.instruments:
            self.instrument_selector.addItem("Nenhum")
            self.status_label.setText("Nenhum instrumento conectado")
            self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        else:
            self.status_label.setText(f"{len(self.instruments)} instrumento(s) conectado(s)")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            for name, info in self.instruments.items():
                # Add to selector
                self.instrument_selector.addItem(name)

                # Add to list
                item_text = f"{name}: {info['model']} ({info['address']})"
                self.instruments_list.addItem(item_text)

            # Try to restore previous selection if it still exists
            index = self.instrument_selector.findText(current_selection)
            if index >= 0:
                self.instrument_selector.setCurrentIndex(index)
            else:
                # Select first instrument by default
                self.instrument_selector.setCurrentIndex(0)

    def on_selection_changed(self, instrument_name):
        """Handle active instrument selection change"""
        if instrument_name and instrument_name != "Nenhum":
            self.active_instrument_changed.emit(instrument_name)


class CommandConsoleWidget(QWidget):
    """Widget for manual command input and execution"""

    command_sent = pyqtSignal(str, str)  # instrument_name, command

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_instrument = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the command console UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Console de Comandos Manuais")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Instrument selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Instrumento:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItem("Selecionar instrumento...")
        self.instrument_combo.currentTextChanged.connect(self.on_instrument_changed)
        selection_layout.addWidget(self.instrument_combo)
        layout.addLayout(selection_layout)

        # Command input
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Comando:"))
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Digite o comando SCPI (ex: *IDN?)")
        self.command_input.returnPressed.connect(self.send_command)
        command_layout.addWidget(self.command_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setEnabled(False)
        command_layout.addWidget(self.send_button)
        layout.addLayout(command_layout)

        # Output display
        layout.addWidget(QLabel("Saída:"))
        self.output_display = QTextEdit()
        self.output_display.setMaximumHeight(200)
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("background-color: #f0f0f0; font-family: 'Courier New';")
        layout.addWidget(self.output_display)

        # Clear button
        self.clear_button = QPushButton("Limpar Console")
        self.clear_button.clicked.connect(self.clear_output)
        layout.addWidget(self.clear_button)

    def add_instrument(self, name):
        """Add instrument to selection"""
        self.instrument_combo.addItem(name)

    def remove_instrument(self, name):
        """Remove instrument from selection"""
        index = self.instrument_combo.findText(name)
        if index >= 0:
            self.instrument_combo.removeItem(index)

    def on_instrument_changed(self, instrument_name):
        """Handle instrument selection change"""
        if instrument_name and instrument_name != "Selecionar instrumento...":
            self.current_instrument = instrument_name
            self.send_button.setEnabled(True)
            self.command_input.setEnabled(True)
        else:
            self.current_instrument = None
            self.send_button.setEnabled(False)
            self.command_input.setEnabled(False)

    def send_command(self):
        """Send command to selected instrument"""
        if not self.current_instrument:
            return

        command = self.command_input.text().strip()
        if not command:
            return

        # Add to output display
        self.output_display.append(f"> {command}")

        # Emit signal to send command
        self.command_sent.emit(self.current_instrument, command)

        # Clear input
        self.command_input.clear()

    def add_response(self, response):
        """Add command response to output"""
        self.output_display.append(f"< {response}")
        self.output_display.append("")  # Empty line for readability

    def clear_output(self):
        """Clear the output display"""
        self.output_display.clear()


class MainWindowV2(QMainWindow):
    """Main application window - Version 2.0 with modern interface"""

    def __init__(self, user_manager=None, config_manager=None, parent=None):
        super().__init__(parent)

        self.user_manager = user_manager
        self.config_manager = config_manager
        self.logger = get_logger(user_manager.current_user if user_manager else None)

        self.connected_instruments = {}
        self.measurement_widgets = {}
        self.active_instrument = None  # Track which instrument is currently active
        self.current_mode = "single"  # Track current operation mode
        self.esp32_device = None  # Track connected ESP32 device

        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.apply_styling()

        self.logger.info("MainWindow v2.0 initialized")

    def setup_ui(self):
        """Setup the main user interface"""
        # Set window title with username
        if self.user_manager and self.user_manager.current_user:
            user_info = self.user_manager.get_current_user_info()
            username_display = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}"
            self.setWindowTitle(f"Keithley LabNano3D v2.0 - {username_display}")
            self.user_display_name = username_display
        else:
            self.setWindowTitle("Keithley LabNano3D v2.0")
            self.user_display_name = "Usuário"

        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Mode selection section (shown after login, before instrument connection)
        self.mode_selection_widget = ModeSelectionWidget(self.user_display_name)
        self.mode_selection_widget.mode_selected.connect(self.on_mode_selected)
        main_layout.addWidget(self.mode_selection_widget)

        # Main splitter (hidden initially, shown after mode selection)
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Collapsible sidebar with instrument status and management
        self.sidebar = CollapsibleSidebar("Instrumentos")

        # Add instrument status to sidebar
        self.instrument_status = InstrumentStatusWidget()
        self.instrument_status.active_instrument_changed.connect(self.on_active_instrument_changed)
        self.sidebar.add_widget(self.instrument_status)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.sidebar.add_widget(separator)

        # Add instrument management to sidebar
        debug_mode = self.config_manager.get_app_config().debug_mode if self.config_manager else False
        self.instrument_management = InstrumentManagementWidget(debug_mode=debug_mode, show_esp32=False)
        self.instrument_management.instrument_connected.connect(self.on_instrument_connected)
        self.instrument_management.esp32_connected.connect(self.on_esp32_connected)
        self.sidebar.add_widget(self.instrument_management)

        self.sidebar.add_stretch()

        self.main_splitter.addWidget(self.sidebar)

        # Right panel - Tabbed interface
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Main tabs for all features (full window usage)
        self.main_tabs = QTabWidget()

        # Tab 1: Measurements
        measurements_tab = QWidget()
        measurements_layout = QVBoxLayout(measurements_tab)
        measurements_layout.setContentsMargins(5, 5, 5, 5)

        # Measurement control widget
        self.measurement_control = MeasurementControlWidget()
        self.measurement_control.measurement_changed.connect(self.on_measurement_type_changed)
        measurements_layout.addWidget(self.measurement_control)

        # Stacked widget for measurement displays
        from PyQt5.QtWidgets import QStackedWidget
        self.measurement_stack = QStackedWidget()
        measurements_layout.addWidget(self.measurement_stack)

        # Add placeholder
        placeholder = QLabel("Conecte um instrumento para começar")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 16px; font-style: italic;")
        self.measurement_stack.addWidget(placeholder)

        self.main_tabs.addTab(measurements_tab, "📊 Medições")

        # Tab 2: Manual Commands
        self.command_console = CommandConsoleWidget()
        self.command_console.command_sent.connect(self.handle_manual_command)
        self.main_tabs.addTab(self.command_console, "🔧 Comandos Manuais")

        # Tab 3: Script Editor
        self.script_editor = ScriptEditorWidget(user_manager=self.user_manager)
        self.script_editor.script_executed.connect(self.handle_script_execution)
        self.main_tabs.addTab(self.script_editor, "📝 Editor de Scripts")

        right_layout.addWidget(self.main_tabs)

        self.main_splitter.addWidget(right_panel)

        # Set splitter proportions (adjusted for wider left panel with instrument management)
        self.main_splitter.setSizes([400, 1000])

        main_layout.addWidget(self.main_splitter)

        # Initially hide main interface until mode is selected
        self.main_splitter.hide()

    def on_mode_selected(self, mode):
        """Handle mode selection"""
        if mode == "new_measurement":
            # Switch to measurement mode
            self.mode_selection_widget.hide()
            self.main_splitter.show()
            # Enable ESP32 tab (always available)
            self.instrument_management.enable_esp32_tab()
            # Instrument management is now embedded in left panel
        elif mode == "load_data":
            # Open data loading dialog
            self.load_data()
            # Stay on mode selection screen

    def on_active_instrument_changed(self, instrument_name):
        """Handle active instrument selection change"""
        self.active_instrument = instrument_name
        self.logger.info(f"Active instrument changed to: {instrument_name}")
        self.status_bar.showMessage(f"Instrumento ativo: {instrument_name}")

        # Update script editor
        self.script_editor.set_instrument(instrument_name)

        # Switch to the measurement widgets for this instrument
        if instrument_name in self.measurement_widgets:
            self.switch_to_instrument_widgets(instrument_name)

    def on_measurement_type_changed(self, measurement_type):
        """Handle measurement type selection change"""
        if not self.active_instrument:
            return

        if self.active_instrument in self.measurement_widgets:
            widgets_dict = self.measurement_widgets[self.active_instrument]
            if measurement_type in widgets_dict:
                # Switch to the selected measurement widget
                self.measurement_stack.setCurrentWidget(widgets_dict[measurement_type])
                self.logger.info(f"Switched to {measurement_type} measurement")

    def switch_to_instrument_widgets(self, instrument_name):
        """Switch the measurement stack to show widgets for the specified instrument"""
        if instrument_name in self.measurement_widgets:
            widgets_dict = self.measurement_widgets[instrument_name]
            # Get current selection from measurement control
            current_type = self.measurement_control.measurement_selector.currentData()
            if current_type and current_type in widgets_dict:
                self.measurement_stack.setCurrentWidget(widgets_dict[current_type])

    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('Arquivo')

        # New measurement
        new_action = QAction('Nova Medição', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_measurement)
        file_menu.addAction(new_action)

        # Load data
        load_action = QAction('Carregar Dados', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_data)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        # Switch user
        switch_user_action = QAction('Trocar Usuário', self)
        switch_user_action.triggered.connect(self.switch_user)
        file_menu.addAction(switch_user_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Instruments menu
        instruments_menu = menubar.addMenu('Instrumentos')

        # Disconnect all
        disconnect_action = QAction('Desconectar Todos', self)
        disconnect_action.triggered.connect(self.disconnect_all_instruments)
        instruments_menu.addAction(disconnect_action)

        # Help menu
        help_menu = menubar.addMenu('Ajuda')

        # About
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_bar.showMessage("Pronto - Nenhum instrumento conectado")

    def apply_styling(self):
        """Apply modern styling to the interface"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #f5f5f5;
            }
        """)

    def on_instrument_connected(self, instrument_info):
        """Handle successful instrument connection"""
        name = instrument_info['name']
        model = instrument_info['model']
        address = instrument_info['address']
        instrument = instrument_info['instrument']
        device_type = instrument_info.get('device_type', 'unknown')

        # Add to connected instruments
        self.connected_instruments[name] = instrument_info

        # Update UI
        self.instrument_status.add_instrument(name, model, address)
        self.command_console.add_instrument(name)
        self.script_editor.add_instrument(name)  # Add to script editor

        # Set as active instrument if it's the first one
        if not self.active_instrument:
            self.active_instrument = name
            self.script_editor.set_instrument(name)  # Set in script editor too

        # Hide mode selection and show main interface if not already shown
        if self.mode_selection_widget.isVisible():
            self.mode_selection_widget.hide()
            self.main_splitter.show()

        # Create measurement tab with appropriate widget
        self.create_measurement_tab_for_instrument(name, instrument, device_type)

        # Update status bar
        count = len(self.connected_instruments)
        self.status_bar.showMessage(f"{count} instrumento(s) conectado(s) | Ativo: {self.active_instrument}")

        self.logger.info(f"Instrument connected: {name} ({model})")

    def create_measurement_tab_for_instrument(self, instrument_name, instrument, device_type):
        """Create measurement widgets for the instrument and add to stack"""
        # Create widgets dict to store different measurement types
        widgets_dict = {}

        # Check if in combined mode with ESP32
        if self.current_mode == "instrument_esp32" and self.esp32_device:
            # Create combined measurement widget
            self.logger.info(f"Creating combined measurement widget for {device_type}")
            from widgets.combined_measurement_widget import CombinedMeasurementWidget
            combined_widget = CombinedMeasurementWidget(
                instrument,
                self.esp32_device,
                device_type=device_type,  # Pass device type
                user_manager=self.user_manager
            )
            widgets_dict['combined'] = combined_widget
            widgets_dict['resistance'] = combined_widget  # Also add as resistance for compatibility
            widgets_dict['iv'] = combined_widget  # Also add as iv for compatibility
            self.logger.info(f"Combined measurement widget created successfully for {device_type}")

        elif device_type == "smu_2450" or "2450" in instrument_name.upper():
            # Create individual measurement widgets
            widgets_dict['resistance'] = ResistanceMeasurementBlock(instrument, user_manager=self.user_manager)
            widgets_dict['iv'] = IVMeasurementBlock(instrument, user_manager=self.user_manager)

        elif device_type == "pico_6487" or "6487" in instrument_name.upper():
            # Create individual measurement widgets for Picoammeter
            widgets_dict['resistance'] = Pico6487ResistanceBlock(instrument, user_manager=self.user_manager)
            widgets_dict['iv'] = Pico6487IVBlock(instrument, user_manager=self.user_manager)
            widgets_dict['charge_discharge'] = Pico6487ChargeDischargeBlock(
                instrument, user_manager=self.user_manager
            )
            from widgets.pico_6487.block_cyclic_voltammetry import CyclicVoltammetryBlock
            widgets_dict['cyclic_voltammetry'] = CyclicVoltammetryBlock(instrument, user_manager=self.user_manager)
            widgets_dict['source'] = Pico6487SourceControlBlock(instrument)


        else:
            # Unknown instrument - create placeholder
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QLabel(f"Widget não disponível para {instrument_name}"))
            layout.addWidget(QLabel("Use o console de comandos manuais para controlar este instrumento."))
            widgets_dict['resistance'] = placeholder
            widgets_dict['iv'] = placeholder

        # Add all widgets to the stack
        for measurement_type, widget in widgets_dict.items():
            self.measurement_stack.addWidget(widget)

        # Store widget references
        self.measurement_widgets[instrument_name] = widgets_dict

        # If this is the active instrument, show its widgets
        if instrument_name == self.active_instrument:
            self.switch_to_instrument_widgets(instrument_name)

        mode_info = "combined mode" if self.current_mode == "instrument_esp32" else f"type: {device_type}"
        self.logger.info(f"Created measurement widgets for {instrument_name} ({mode_info})")

    def on_esp32_connected(self, device):
        """Handle ESP32 device connection"""
        self.esp32_device = device
        self.logger.info(f"ESP32 connected on {device.port}")
        self.logger.info(f"Current active instrument: {self.active_instrument}")
        self.logger.info(f"Connected instruments: {list(self.connected_instruments.keys())}")

        # Update status bar
        instruments_count = len(self.connected_instruments)
        self.status_bar.showMessage(
            f"{instruments_count} instrumento(s) conectado(s) | ESP32: {device.port} | Ativo: {self.active_instrument}"
        )

        # Show dialog to choose ESP32 usage mode
        from widgets.esp32_mode_dialog import ESP32ModeDialog

        has_visa = self.active_instrument is not None and self.active_instrument in self.connected_instruments
        self.logger.info(f"Has VISA instrument: {has_visa}")
        dialog = ESP32ModeDialog(has_visa_instrument=has_visa, parent=self)

        if dialog.exec_() == QDialog.Accepted:
            mode = dialog.get_selected_mode()
            self.logger.info(f"ESP32 mode selected: {mode}")

            if mode == 'standalone':
                # Create standalone ESP32 measurement window
                self.create_esp32_standalone_measurement()
            elif mode == 'add_to_visa' and has_visa:
                # Add ESP32 to existing VISA instrument measurements
                self.add_esp32_to_visa_measurements()
            else:
                self.logger.warning("No valid mode selected for ESP32")
        else:
            # User canceled - disconnect ESP32
            self.logger.info("ESP32 mode selection canceled")
            # Optionally disconnect ESP32 here if desired

    def create_esp32_standalone_measurement(self):
        """Create standalone ESP32 measurement widget"""
        from widgets.esp32_standalone_measurement import ESP32StandaloneMeasurementWidget

        # Create standalone measurement widget
        esp32_widget = ESP32StandaloneMeasurementWidget(
            self.esp32_device,
            user_manager=self.user_manager
        )

        # Add to measurement stack or create new tab/window
        # For now, let's replace the current measurement view
        self.measurement_stack.addWidget(esp32_widget)
        self.measurement_stack.setCurrentWidget(esp32_widget)

        # Store reference
        self.esp32_standalone_widget = esp32_widget

        self.logger.info("Created standalone ESP32 measurement widget")
        QMessageBox.information(
            self,
            "ESP32 Configurado",
            "Janela de medição ESP32 criada com sucesso!\n\n"
            "Configure os parâmetros e clique em 'Iniciar Medição'."
        )

    def add_esp32_to_visa_measurements(self):
        """Add ESP32 readings to VISA instrument measurements"""
        self.logger.info("add_esp32_to_visa_measurements called")
        if not self.active_instrument or self.active_instrument not in self.connected_instruments:
            self.logger.error("No active VISA instrument to add ESP32")
            QMessageBox.warning(
                self,
                "Erro",
                "Nenhum instrumento VISA ativo para adicionar ESP32."
            )
            return

        # Set mode to combined
        self.logger.info(f"Setting mode to instrument_esp32 (was: {self.current_mode})")
        self.current_mode = "instrument_esp32"

        # Recreate measurement widgets for the active instrument with combined mode
        instrument_info = self.connected_instruments[self.active_instrument]
        instrument = instrument_info['instrument']
        device_type = instrument_info.get('device_type', 'unknown')
        self.logger.info(f"Active instrument: {self.active_instrument}, device_type: {device_type}")

        # Clear old widgets
        if self.active_instrument in self.measurement_widgets:
            old_widgets = self.measurement_widgets[self.active_instrument]
            self.logger.info(f"Clearing {len(old_widgets)} old widgets")
            for widget_name, widget in old_widgets.items():
                self.logger.debug(f"Removing widget: {widget_name}")
                self.measurement_stack.removeWidget(widget)
                widget.deleteLater()

        # Create new combined widgets
        self.logger.info("Creating new combined measurement widgets")
        self.create_measurement_tab_for_instrument(
            self.active_instrument,
            instrument,
            device_type
        )

        self.logger.info("Added ESP32 to VISA instrument measurements successfully")
        QMessageBox.information(
            self,
            "ESP32 Adicionado",
            "ESP32 adicionado ao instrumento VISA com sucesso!\n\n"
            "As medições serão realizadas simultaneamente com dois eixos Y."
        )

    def handle_manual_command(self, instrument_name, command):
        """Handle manual command execution"""
        if instrument_name not in self.connected_instruments:
            return

        instrument_info = self.connected_instruments[instrument_name]
        instrument = instrument_info['instrument']

        try:
            if command.endswith('?'):
                # Query command
                response = instrument.query(command)
                self.command_console.add_response(response)
            else:
                # Write command
                instrument.write(command)
                self.command_console.add_response("OK")

        except Exception as e:
            self.command_console.add_response(f"ERROR: {e}")
            self.logger.error(f"Manual command failed: {command} -> {e}")

    def new_measurement(self):
        """Not used in v2.1 - measurements are selected via measurement control widget"""
        # Keeping for menu compatibility but showing info message
        QMessageBox.information(
            self,
            "Seleção de Medição",
            "Use o seletor 'Tipo de Medição' acima da área de medição para escolher a função disponível para o instrumento."
        )
    
    def load_data(self):
        """Load data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Dados",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implement data loading
            QMessageBox.information(self, "Carregar Dados", 
                                  f"Funcionalidade em desenvolvimento.\nArquivo: {file_path}")
    
    def handle_script_execution(self, instrument_name, script_content):
        """Execute a script on the specified instrument"""
        if instrument_name not in self.connected_instruments:
            self.script_editor.add_output(f"Erro: Instrumento '{instrument_name}' não conectado.")
            return
        
        instrument_info = self.connected_instruments[instrument_name]
        instrument = instrument_info['instrument']
        
        # Split script into lines and execute each command
        lines = script_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                self.script_editor.add_output(f"[{i}] > {line}")
                
                if line.endswith('?') or 'READ' in line.upper() or 'PRINT' in line.upper():
                    # Query command or read command - show actual equipment response
                    try:
                        response = instrument.query(line)
                        # Display the actual response from the equipment
                        self.script_editor.add_output(f"    < {response.strip()}")
                    except Exception as query_error:
                        # If query fails, try as write command
                        instrument.write(line)
                        self.script_editor.add_output(f"    ✓ Comando enviado")
                else:
                    # Write command
                    instrument.write(line)
                    self.script_editor.add_output(f"    ✓ OK")
            
            except Exception as e:
                self.script_editor.add_output(f"    ✗ ERRO: {e}")
                # Continue executing remaining commands instead of breaking
        
        self.script_editor.add_output(f"\n{'='*60}")
        self.script_editor.add_output("Script concluído.")
        self.script_editor.add_output(f"{'='*60}\n")
    
    def disconnect_all_instruments(self):
        """Disconnect all instruments"""
        for name, instrument_info in self.connected_instruments.items():
            try:
                instrument = instrument_info['instrument']
                if hasattr(instrument, 'close'):
                    instrument.close()
            except Exception as e:
                self.logger.error(f"Error disconnecting {name}: {e}")
        
        self.connected_instruments.clear()
        self.instrument_status.instruments.clear()
        self.instrument_status.update_display()
        
        # Clear command console
        self.command_console.instrument_combo.clear()
        self.command_console.instrument_combo.addItem("Selecionar instrumento...")
        
        # Show mode selection screen
        self.main_splitter.hide()
        self.mode_selection_widget.show()
        
        self.status_bar.showMessage("Todos os instrumentos desconectados")
        self.logger.info("All instruments disconnected")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "Sobre", 
                         "Keithley LabNano3D v2.0\n\n"
                         "Sistema de Controle de Instrumentos\n"
                         "para Nanotecnologia\n\n"
                         "Desenvolvido pela equipe LabNano3D")
    
    def switch_user(self):
        """Switch to a different user (logout and return to login screen)"""
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Trocar Usuário",
            "Tem certeza que deseja trocar de usuário?\n\n"
            "Todos os instrumentos serão desconectados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Disconnect all instruments
            self.disconnect_all_instruments()
            
            # Close this window
            self.close()
            
            # Open startup window again
            from startup_window import main as startup_main
            startup_main()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Disconnect all instruments safely
        self.disconnect_all_instruments()
        
        self.logger.info("MainWindow closed")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindowV2()
    window.show()
    sys.exit(app.exec_())