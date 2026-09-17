"""
Script Editor Widget for Keithley LabNano3D
Allows users to create, edit, and execute scripts for instruments
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QListWidget, QLabel, QFileDialog, QMessageBox, QSplitter, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from pathlib import Path


class ScriptEditorWidget(QWidget):
    """Widget for editing and executing instrument scripts"""
    
    script_executed = pyqtSignal(str, str)  # Emits (instrument_name, script_content)
    
    def __init__(self, user_manager=None, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_instrument = None
        self.current_script_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the script editor UI"""
        layout = QVBoxLayout(self)
        
        # Top toolbar
        toolbar = QHBoxLayout()
        
        # Instrument selector
        toolbar.addWidget(QLabel("Instrumento:"))
        self.instrument_selector = QComboBox()
        self.instrument_selector.addItem("Nenhum")
        self.instrument_selector.currentTextChanged.connect(self.on_instrument_changed)
        toolbar.addWidget(self.instrument_selector)
        
        toolbar.addStretch()
        
        # Script management buttons
        self.btn_new = QPushButton("Novo Script")
        self.btn_new.clicked.connect(self.new_script)
        toolbar.addWidget(self.btn_new)
        
        self.btn_load = QPushButton("Carregar")
        self.btn_load.clicked.connect(self.load_script)
        toolbar.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("Salvar")
        self.btn_save.clicked.connect(self.save_script)
        toolbar.addWidget(self.btn_save)
        
        self.btn_save_as = QPushButton("Salvar Como...")
        self.btn_save_as.clicked.connect(self.save_script_as)
        toolbar.addWidget(self.btn_save_as)
        
        layout.addLayout(toolbar)
        
        # Main area - splitter for editor and output
        splitter = QSplitter(Qt.Vertical)
        
        # Script editor
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Editor de Script:")
        editor_label.setStyleSheet("font-weight: bold;")
        editor_layout.addWidget(editor_label)
        
        self.script_editor = QTextEdit()
        self.script_editor.setPlaceholderText(
            "# Digite seu script aqui\n"
            "# Exemplo para SMU 2450:\n"
            "# *RST\n"
            "# :SOUR:FUNC VOLT\n"
            "# :SOUR:VOLT 1.0\n"
            "# :OUTP ON\n"
            "# :READ?\n"
        )
        
        # Monospace font for code
        font = QFont("Courier New", 10)
        self.script_editor.setFont(font)
        editor_layout.addWidget(self.script_editor)
        
        splitter.addWidget(editor_container)
        
        # Output terminal
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        output_label = QLabel("Terminal de Saída:")
        output_label.setStyleSheet("font-weight: bold;")
        output_layout.addWidget(output_label)
        
        self.output_terminal = QTextEdit()
        self.output_terminal.setReadOnly(True)
        self.output_terminal.setFont(font)
        self.output_terminal.setPlaceholderText("Saída do script aparecerá aqui...")
        output_layout.addWidget(self.output_terminal)
        
        # Output buttons
        output_buttons = QHBoxLayout()
        
        self.btn_clear_output = QPushButton("Limpar Saída")
        self.btn_clear_output.clicked.connect(self.clear_output)
        output_buttons.addWidget(self.btn_clear_output)
        
        self.btn_export_output = QPushButton("Exportar Saída")
        self.btn_export_output.clicked.connect(self.export_output)
        output_buttons.addWidget(self.btn_export_output)
        
        output_buttons.addStretch()
        
        self.btn_execute = QPushButton("Executar Script")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_execute.clicked.connect(self.execute_script)
        output_buttons.addWidget(self.btn_execute)
        
        output_layout.addLayout(output_buttons)
        
        splitter.addWidget(output_container)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
    
    def set_instrument(self, instrument_name):
        """Set the active instrument"""
        self.current_instrument = instrument_name
        index = self.instrument_selector.findText(instrument_name)
        if index >= 0:
            self.instrument_selector.setCurrentIndex(index)
    
    def add_instrument(self, instrument_name):
        """Add instrument to selector"""
        if self.instrument_selector.findText(instrument_name) < 0:
            self.instrument_selector.addItem(instrument_name)
    
    def on_instrument_changed(self, instrument_name):
        """Handle instrument selection change"""
        if instrument_name and instrument_name != "Nenhum":
            self.current_instrument = instrument_name
        else:
            self.current_instrument = None
    
    def new_script(self):
        """Create a new script"""
        if self.script_editor.toPlainText().strip():
            reply = QMessageBox.question(
                self,
                "Novo Script",
                "Descartar o script atual?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.script_editor.clear()
        self.current_script_path = None
    
    def load_script(self):
        """Load a script from file"""
        if not self.user_manager or not self.user_manager.current_user:
            QMessageBox.warning(self, "Erro", "Nenhum usuário logado.")
            return
        
        # Get scripts directory for current instrument
        if self.current_instrument:
            # Determine instrument type folder
            instrument_folder = "smu_2450" if "2450" in self.current_instrument else "pico_6487"
            scripts_dir = self.user_manager.get_user_directory("scripts") / instrument_folder
        else:
            scripts_dir = self.user_manager.get_user_directory("scripts")
        
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Script",
            str(scripts_dir),
            "Script Files (*.txt *.py *.scpi);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.script_editor.setPlainText(content)
                self.current_script_path = Path(file_path)
                self.add_output(f"Script carregado: {Path(file_path).name}")
            
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar script: {e}")
    
    def save_script(self):
        """Save the current script"""
        if self.current_script_path:
            self._save_to_path(self.current_script_path)
        else:
            self.save_script_as()
    
    def save_script_as(self):
        """Save the script with a new name"""
        if not self.user_manager or not self.user_manager.current_user:
            QMessageBox.warning(self, "Erro", "Nenhum usuário logado.")
            return
        
        # Get scripts directory for current instrument
        if self.current_instrument:
            instrument_folder = "smu_2450" if "2450" in self.current_instrument else "pico_6487"
            scripts_dir = self.user_manager.get_user_directory("scripts") / instrument_folder
        else:
            scripts_dir = self.user_manager.get_user_directory("scripts")
        
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Script Como",
            str(scripts_dir / "script.txt"),
            "Script Files (*.txt *.py *.scpi);;All Files (*.*)"
        )
        
        if file_path:
            self._save_to_path(Path(file_path))
    
    def _save_to_path(self, file_path):
        """Save script to specified path"""
        try:
            content = self.script_editor.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.current_script_path = file_path
            self.add_output(f"Script salvo: {file_path.name}")
            QMessageBox.information(self, "Sucesso", "Script salvo com sucesso!")
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar script: {e}")
    
    def execute_script(self):
        """Execute the current script"""
        if not self.current_instrument:
            QMessageBox.warning(
                self,
                "Nenhum Instrumento",
                "Selecione um instrumento antes de executar o script."
            )
            return
        
        script_content = self.script_editor.toPlainText().strip()
        if not script_content:
            QMessageBox.warning(self, "Script Vazio", "Digite um script antes de executar.")
            return
        
        self.add_output(f"\n{'='*60}")
        self.add_output(f"Executando script no instrumento: {self.current_instrument}")
        self.add_output(f"{'='*60}\n")
        
        # Emit signal to main window to execute the script
        self.script_executed.emit(self.current_instrument, script_content)
    
    def add_output(self, text):
        """Add text to output terminal"""
        self.output_terminal.append(text)
        # Scroll to bottom
        cursor = self.output_terminal.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output_terminal.setTextCursor(cursor)
    
    def clear_output(self):
        """Clear the output terminal"""
        self.output_terminal.clear()
    
    def export_output(self):
        """Export output to file"""
        if not self.user_manager or not self.user_manager.current_user:
            QMessageBox.warning(self, "Erro", "Nenhum usuário logado.")
            return
        
        exports_dir = self.user_manager.get_user_directory("exports")
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Saída",
            str(exports_dir / "script_output.txt"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                content = self.output_terminal.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(self, "Sucesso", "Saída exportada com sucesso!")
            
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar saída: {e}")
