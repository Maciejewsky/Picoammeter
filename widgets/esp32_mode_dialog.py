"""
ESP32 Mode Selection Dialog
Allows user to choose between standalone ESP32 measurements or adding to VISA instrument
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ESP32ModeDialog(QDialog):
    """Dialog for selecting ESP32 usage mode"""
    
    def __init__(self, has_visa_instrument=False, parent=None):
        super().__init__(parent)
        self.has_visa_instrument = has_visa_instrument
        self.selected_mode = None  # Will be 'standalone' or 'add_to_visa'
        
        self.setWindowTitle("Configuração ESP32")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("ESP32 Conectado com Sucesso!")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Como deseja utilizar o ESP32?")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666666;")
        layout.addWidget(subtitle)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Radio button group
        self.mode_group = QButtonGroup(self)
        
        # Option 1: Standalone ESP32
        self.radio_standalone = QRadioButton("Apenas ESP32 (Medição Independente)")
        self.radio_standalone.setStyleSheet("""
            QRadioButton {
                font-size: 13px;
                padding: 10px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.mode_group.addButton(self.radio_standalone, 0)
        layout.addWidget(self.radio_standalone)
        
        # Description for standalone
        standalone_desc = QLabel(
            "• Cria uma janela de medição independente para o ESP32/ADS1115\n"
            "• Gráfico com tempo vs. leitura do sensor\n"
            "• Exportação em formato: tempo, leitura\n"
            "• Ideal para medições exclusivas de sensores"
        )
        standalone_desc.setStyleSheet("font-size: 11px; color: #555555; margin-left: 30px; margin-bottom: 10px;")
        standalone_desc.setWordWrap(True)
        layout.addWidget(standalone_desc)
        
        # Option 2: Add to VISA (only if VISA instrument is connected)
        if self.has_visa_instrument:
            self.radio_add_to_visa = QRadioButton("Adicionar ao Instrumento VISA")
            self.radio_add_to_visa.setStyleSheet("""
                QRadioButton {
                    font-size: 13px;
                    padding: 10px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
            """)
            self.mode_group.addButton(self.radio_add_to_visa, 1)
            layout.addWidget(self.radio_add_to_visa)
            
            # Description for add to VISA
            add_to_visa_desc = QLabel(
                "• Adiciona leituras ESP32 à janela do instrumento VISA\n"
                "• Gráfico com dois eixos Y (VISA + ESP32)\n"
                "• Medições simultâneas no mesmo intervalo\n"
                "• Exportação em formato: tempo, leitura VISA, leitura ESP32\n"
                "• Ideal para correlacionar medições elétricas com sensores"
            )
            add_to_visa_desc.setStyleSheet("font-size: 11px; color: #555555; margin-left: 30px; margin-bottom: 10px;")
            add_to_visa_desc.setWordWrap(True)
            layout.addWidget(add_to_visa_desc)
            
            # Set as default if VISA is connected
            self.radio_add_to_visa.setChecked(True)
        else:
            # Only option is standalone
            self.radio_standalone.setChecked(True)
            
            # Info message
            info = QLabel("⚠️ Nenhum instrumento VISA conectado. Apenas medição ESP32 disponível.")
            info.setStyleSheet("font-size: 12px; color: #FF9800; padding: 10px; background-color: #FFF3E0; border-radius: 5px;")
            info.setWordWrap(True)
            layout.addWidget(info)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("Confirmar")
        self.btn_ok.setMinimumWidth(100)
        self.btn_ok.setStyleSheet("""
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
        self.btn_ok.clicked.connect(self.accept_selection)
        button_layout.addWidget(self.btn_ok)
        
        layout.addLayout(button_layout)
    
    def accept_selection(self):
        """Accept the selected mode"""
        if self.radio_standalone.isChecked():
            self.selected_mode = 'standalone'
        elif self.has_visa_instrument and self.radio_add_to_visa.isChecked():
            self.selected_mode = 'add_to_visa'
        else:
            self.selected_mode = 'standalone'
        
        self.accept()
    
    def get_selected_mode(self):
        """Get the selected mode"""
        return self.selected_mode
