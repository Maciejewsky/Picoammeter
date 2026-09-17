# widgets/smu_2450/block_source_control.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt


class SourceControlBlock(QWidget):
    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument

        self.setLayout(QVBoxLayout())

        # Título
        self.layout().addWidget(QLabel("<b>Controle da Fonte SMU 2450</b>"))

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

        # Campo para limite de corrente
        current_layout = QHBoxLayout()
        self.current_input = QLineEdit()
        self.current_input.setPlaceholderText("Limite de corrente (A)")
        self.current_input.setFixedWidth(120)
        btn_set_current = QPushButton("Aplicar")
        btn_set_current.clicked.connect(self.set_current_limit)
        current_layout.addWidget(self.current_input)
        current_layout.addWidget(btn_set_current)
        self.layout().addLayout(current_layout)

        # Botão estilo chave (toggle)
        self.toggle_button = QPushButton("Fonte OFF")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet(self._get_style(False))
        self.toggle_button.clicked.connect(self.toggle_source)
        self.layout().addWidget(self.toggle_button, alignment=Qt.AlignLeft)

        # Configuração inicial do SMU
        self.initialize_smu()

    def initialize_smu(self):
        """Configura o 2450 para modo fonte de tensão e medida de corrente."""
        try:
            self.instrument.write("smu.reset()")
            self.instrument.write("smu.source.func = smu.FUNC_DC_VOLTAGE")
            self.instrument.write("smu.measure.func = smu.FUNC_DC_CURRENT")
            self.instrument.write("smu.source.ilimit.level = 1e-3")  # padrão: 1 mA
        except Exception as e:
            print(f"Erro na configuração inicial do SMU: {e}")

    def set_voltage(self):
        """Define a tensão da fonte."""
        try:
            voltage = float(self.voltage_input.text())
        except ValueError:
            self.voltage_input.setText("")
            return

        try:
            self.instrument.write(f"smu.source.level = {voltage}")
        except Exception as e:
            print(f"Erro ao aplicar tensão: {e}")

    def set_current_limit(self):
        """Define o limite de corrente."""
        try:
            current = float(self.current_input.text())
        except ValueError:
            self.current_input.setText("")
            return

        try:
            self.instrument.write(f"smu.source.ilimit.level = {current}")
        except Exception as e:
            print(f"Erro ao aplicar limite de corrente: {e}")

    def toggle_source(self):
        """Liga/desliga a fonte."""
        state = self.toggle_button.isChecked()
        try:
            if state:
                self.instrument.write("smu.source.output = smu.ON")
                self.toggle_button.setText("Fonte ON")
            else:
                self.instrument.write("smu.source.output = smu.OFF")
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
