"""
Startup window for Keithley LabNano3D
Handles user login, initial setup, and application entry point
"""

import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QComboBox, QCheckBox, QMessageBox, QApplication, QWidget,
    QGridLayout, QSpacerItem, QSizePolicy, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPalette

from core.user_manager import get_user_manager
from core.config import get_config_manager
from core.logger import init_logging
from main_window_v2 import MainWindowV2


class UserLoginWidget(QWidget):
    """Widget for user login/registration"""
    
    user_selected = pyqtSignal(str)  # Emits username when user is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = get_user_manager()
        self.setup_ui()
        self.load_existing_users()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Bem-vindo ao Keithley LabNano3D")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Sistema de Controle de Instrumentos para Nanotecnologia")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Existing users section
        existing_group = QGroupBox("Usuários Existentes")
        existing_layout = QVBoxLayout(existing_group)
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumHeight(35)
        existing_layout.addWidget(QLabel("Selecionar usuário:"))
        existing_layout.addWidget(self.user_combo)
        
        self.btn_login_existing = QPushButton("Entrar")
        self.btn_login_existing.setMinimumHeight(35)
        self.btn_login_existing.clicked.connect(self.login_existing_user)
        existing_layout.addWidget(self.btn_login_existing)
        
        layout.addWidget(existing_group)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # New user section
        new_user_group = QGroupBox("Novo Usuário")
        new_user_layout = QGridLayout(new_user_group)
        
        # First name
        new_user_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setMinimumHeight(35)
        self.first_name_edit.setPlaceholderText("Digite seu nome")
        new_user_layout.addWidget(self.first_name_edit, 0, 1)
        
        # Last name
        new_user_layout.addWidget(QLabel("Sobrenome:"), 1, 0)
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setMinimumHeight(35)
        self.last_name_edit.setPlaceholderText("Digite seu sobrenome")
        new_user_layout.addWidget(self.last_name_edit, 1, 1)
        
        # Create user button
        self.btn_create_user = QPushButton("Criar Usuário")
        self.btn_create_user.setMinimumHeight(35)
        self.btn_create_user.clicked.connect(self.create_new_user)
        new_user_layout.addWidget(self.btn_create_user, 2, 0, 1, 2)
        
        layout.addWidget(new_user_group)
        
        # Make sure first name field gets focus
        self.first_name_edit.returnPressed.connect(self.last_name_edit.setFocus)
        self.last_name_edit.returnPressed.connect(self.create_new_user)
    
    def load_existing_users(self):
        """Load existing users into combo box"""
        users = self.user_manager.list_users()
        self.user_combo.clear()
        
        if not users:
            self.user_combo.addItem("Nenhum usuário encontrado")
            self.btn_login_existing.setEnabled(False)
        else:
            for user in users:
                display_name = f"{user['first_name']} {user['last_name']} ({user['username']})"
                self.user_combo.addItem(display_name, user['username'])
            self.btn_login_existing.setEnabled(True)
    
    def login_existing_user(self):
        """Login with existing user"""
        current_data = self.user_combo.currentData()
        if current_data:
            username = current_data
            if self.user_manager.login_user(username):
                self.user_selected.emit(username)
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível fazer login com este usuário.")
    
    def create_new_user(self):
        """Create new user"""
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        
        if not first_name or not last_name:
            QMessageBox.warning(self, "Campos Obrigatórios", 
                              "Por favor, preencha nome e sobrenome.")
            return
        
        try:
            username = self.user_manager.create_user_profile(first_name, last_name)
            self.user_selected.emit(username)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar usuário: {e}")


class DebugPasswordDialog(QDialog):
    """Dialog for debug mode password entry"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modo Debug")
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Digite a senha para acessar o modo debug:"))
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Senha")
        layout.addWidget(self.password_edit)
        
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancelar")
        
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)
        
        self.password_edit.returnPressed.connect(self.accept)
    
    def get_password(self):
        """Get entered password"""
        return self.password_edit.text()


class StartupWindow(QDialog):
    """Main startup window for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keithley LabNano3D - Inicialização")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        self.user_manager = get_user_manager()
        self.config_manager = get_config_manager(self.user_manager)
        self.main_window = None
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # User login section
        self.user_widget = UserLoginWidget()
        self.user_widget.user_selected.connect(self.on_user_selected)
        layout.addWidget(self.user_widget)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Debug mode section
        debug_group = QGroupBox("Opções Avançadas")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_checkbox = QCheckBox("Ativar modo debug (instrumentos simulados)")
        debug_layout.addWidget(self.debug_checkbox)
        
        layout.addWidget(debug_group)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.btn_exit = QPushButton("Sair")
        self.btn_exit.clicked.connect(self.reject)
        
        button_layout.addWidget(self.btn_exit)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def apply_styling(self):
        """Apply modern styling to the window"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
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
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QComboBox {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
    
    def on_user_selected(self, username):
        """Handle user selection"""
        # Initialize logging for the user
        logger = init_logging(username)
        logger.info(f"User {username} logged in")
        
        # Load user-specific configuration
        self.config_manager.load_user_config()
        
        # Check if debug mode is requested
        debug_mode = self.debug_checkbox.isChecked()
        if debug_mode:
            if not self.verify_debug_password():
                return
        
        # Update config with debug mode
        self.config_manager.update_app_config(debug_mode=debug_mode)
        
        # Close startup window and open main application
        self.accept()
        self.open_main_application()
    
    def verify_debug_password(self):
        """Verify debug mode password"""
        dialog = DebugPasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            password = dialog.get_password()
            if self.config_manager.verify_debug_password(password):
                return True
            else:
                QMessageBox.warning(self, "Senha Incorreta", 
                                  "Senha do modo debug incorreta.")
                return False
        return False
    
    def open_main_application(self):
        """Open the main application window"""
        try:
            self.main_window = MainWindowV2(
                user_manager=self.user_manager,
                config_manager=self.config_manager
            )
            self.main_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir aplicação principal: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Keithley LabNano3D")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("LabNano3D")
    
    # Create and show startup window
    startup = StartupWindow()
    if startup.exec_() == QDialog.Accepted:
        # User logged in successfully, main window should be open
        return app.exec_()
    else:
        # User cancelled or exited
        return 0


if __name__ == "__main__":
    sys.exit(main())