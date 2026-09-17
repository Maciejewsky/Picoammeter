# widgets/pico_6487/source_control.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt


class SourceControlBlock(QWidget):
    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument

        self.setLayout(QVBoxLayout())

        # Título
        self.layout().addWidget(QLabel("<b>Controle da Fonte de Tensão</b>"))

        # Campo para definir a tensão
        voltage_layout = QHBoxLayout()
        self.voltage_input = QLineEdit()
        self.voltage_input.setPlaceholderText("Digite a tensão (V)")
        self.voltage_input.setFixedWidth(120)
        btn_set_voltage = QPushButton("Aplicar")
        btn_set_voltage.clicked.connect(self.set_voltage)
        voltage_layout.addWidget(self.voltage_input)
        voltage_layout.addWidget(btn_set_voltage)
        self.layout().addLayout(voltage_layout)

        # Botão estilo chave (toggle)
        self.toggle_button = QPushButton("Fonte OFF")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet(self._get_style(False))
        self.toggle_button.clicked.connect(self.toggle_source)
        self.layout().addWidget(self.toggle_button, alignment=Qt.AlignLeft)

    def set_voltage(self):
        """Define a tensão da fonte."""
        try:
            voltage = float(self.voltage_input.text())
        except ValueError:
            self.voltage_input.setText("")
            return

        try:
            self.instrument.write(f"SOUR:VOLT {voltage}")
        except Exception as e:
            print(f"Erro ao aplicar tensão: {e}")

    def toggle_source(self):
        """Liga/desliga a fonte."""
        state = self.toggle_button.isChecked()
        try:
            if state:
                self.instrument.write("SOUR:VOLT:STAT ON")
                self.toggle_button.setText("Fonte ON")
            else:
                self.instrument.write("SOUR:VOLT:STAT OFF")
                self.toggle_button.setText("Fonte OFF")
            self.toggle_button.setStyleSheet(self._get_style(state))
        except Exception as e:
            print(f"Erro ao alterar estado da fonte: {e}")

    def _get_style(self, is_on):
        """Retorna o estilo do botão conforme o estado."""
        if is_on:
            return (
                "background-color: green; color: white; font-weight: bold;"
                "border-radius: 5px; padding: 6px;"
            )
        else:
            return (
                "background-color: red; color: white; font-weight: bold;"
                "border-radius: 5px; padding: 6px;"
            )
