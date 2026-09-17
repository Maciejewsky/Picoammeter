# widgets/pico_6487/block_cyclic_voltammetry.py

from datetime import datetime, timedelta
import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QMessageBox,
    QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg


class CyclicVoltammetryBlock(QWidget):
    _last_params_dir = None
    _last_export_dir = None
    _last_load_dir = None

    def __init__(self, instrument, user_manager=None, parent=None):
        super().__init__(parent)

        self.instrument = instrument
        self.user_manager = user_manager

        self.measuring = False
        self.phase = "IDA"
        self.cycle_count = 0
        self.readings = []
        self.first_reading_time = None
        self.start_time = None
        self.temp_file_path = None

        self.v_current = 0.0
        self.v1_value = 0.0
        self.v2_value = 0.0
        self.step_value = 0.1
        self.direction = 1

        self.measure_timer = QTimer(self)
        self.measure_timer.timeout.connect(self.acquire_reading)

        self._build_ui()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        params_group = QGroupBox("Parâmetros de Voltametria Cíclica")
        params_layout = QVBoxLayout()

        self.v1_spin = self._create_voltage_spin(0.0)
        self._add_row(params_layout, "V1 (Vértice Inicial V):", self.v1_spin)

        self.v2_spin = self._create_voltage_spin(5.0)
        self._add_row(params_layout, "V2 (Vértice de Retorno V):", self.v2_spin)

        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.001, 50.0)
        self.step_spin.setDecimals(3)
        self.step_spin.setValue(0.1)
        self._add_row(params_layout, "Passo (V):", self.step_spin)

        self.scan_rate_spin = QDoubleSpinBox()
        self.scan_rate_spin.setRange(0.001, 10.0)
        self.scan_rate_spin.setDecimals(3)
        self.scan_rate_spin.setValue(0.1)
        self._add_row(params_layout, "Taxa de Varredura (V/s):", self.scan_rate_spin)

        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 1000)
        self.cycles_spin.setValue(1)
        self._add_row(params_layout, "Número de Ciclos:", self.cycles_spin)

        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(2.5e-6, 2.5e-2)
        self.ilim_spin.setDecimals(6)
        self.ilim_spin.setValue(0.025)
        self._add_row(params_layout, "Limite de corrente (A):", self.ilim_spin)

        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.01, 6.0)
        self.nplc_spin.setDecimals(2)
        self.nplc_spin.setValue(1.0)
        self._add_row(params_layout, "NPLC:", self.nplc_spin)

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

        self.toggle_button = QPushButton("Iniciar Voltametria")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_measurement)
        left_layout.addWidget(self.toggle_button)

        self.list_widget = QListWidget()
        left_layout.addWidget(self.list_widget)

        self.stats_label = QLabel("Ciclos: 0 | Tempo: 00:00:00 | Fase: --")
        left_layout.addWidget(self.stats_label)

        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: red; font-weight: bold;")
        left_layout.addWidget(self.alert_label)

        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar Medição")
        self.export_button.clicked.connect(self.export_measurement)
        buttons_layout.addWidget(self.export_button)

        load_measurement_btn = QPushButton("Carregar Medição")
        load_measurement_btn.clicked.connect(self.load_measurement)
        buttons_layout.addWidget(load_measurement_btn)

        left_layout.addLayout(buttons_layout)
        splitter.addWidget(left_widget)

        # Gráfico: Corrente x Tensão (Voltograma)
        self.cv_plot = pg.PlotWidget(title="Voltograma Cíclico (I x V)")
        self.cv_plot.setLabel("left", "Corrente (A)")
        self.cv_plot.setLabel("bottom", "Tensão (V)")
        self.cv_plot.showGrid(x=True, y=True)
        self.cv_curve = self.cv_plot.plot([], [], pen=pg.mkPen(color="g", width=2))

        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(self.cv_plot)

        splitter.addWidget(graph_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    @staticmethod
    def _create_voltage_spin(value):
        spin = QDoubleSpinBox()
        spin.setRange(-505.0, 505.0)
        spin.setDecimals(3)
        spin.setValue(value)
        spin.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        return spin

    @staticmethod
    def _add_row(layout, label, widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(widget)
        layout.addLayout(row)

    # ------------------------------------------------------------------
    # Controle da medição
    # ------------------------------------------------------------------

    def toggle_measurement(self, checked):
        if checked:
            self.start_measurement()
        else:
            self.stop_measurement()

    def start_measurement(self):
        if self.instrument is None:
            self.alert_label.setText("Instrumento não conectado.")
            self._reset_toggle()
            return

        self.v1_value = self.v1_spin.value()
        self.v2_value = self.v2_spin.value()
        self.step_value = abs(self.step_spin.value())
        self.scan_rate = self.scan_rate_spin.value()

        if self.v1_value == self.v2_value:
            QMessageBox.warning(self, "Parâmetros inválidos", "V1 e V2 não podem ser iguais.")
            self._reset_toggle()
            return

        # Calcula o intervalo entre medições em segundos
        self.interval = self.step_value / self.scan_rate
        if self.interval < 0.05:
            QMessageBox.warning(self, "Taxa muito alta",
                                "A combinação de Passo e Taxa resulta em um intervalo menor que 50ms. O 6487 pode não acompanhar.")
            self._reset_toggle()
            return

        self.measuring = True
        self.phase = "IDA"
        self.cycle_count = 0
        self.max_cycles = self.cycles_spin.value()

        self.direction = 1 if self.v2_value > self.v1_value else -1
        self.v_current = self.v1_value

        self.readings.clear()
        self.list_widget.clear()
        self.alert_label.setText("")
        self.first_reading_time = None
        self.start_time = datetime.now()

        self.cv_curve.setData([], [])
        self.toggle_button.setText("Parar Voltametria")

        if self.user_manager:
            try:
                temp_dir = self.user_manager.get_user_directory("measurements/cyclic_voltammetry")
                timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
                self.temp_file_path = temp_dir / f"temp_cv_6487_{timestamp}.txt"
            except Exception:
                self.temp_file_path = None
        else:
            self.temp_file_path = None

        self.configure_instrument_step(0)

    def _reset_toggle(self):
        self.toggle_button.blockSignals(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.blockSignals(False)
        self.toggle_button.setText("Iniciar Voltametria")

    def stop_measurement(self):
        was_measuring = self.measuring
        self.measuring = False
        self.measure_timer.stop()
        self._reset_toggle()

        if self.instrument is not None:
            try:
                self.instrument.write(f"SOUR:VOLT {self.v1_spin.value()}")
                self.instrument.write("SOUR:VOLT:STAT OFF")
            except Exception as exc:
                print(f"Erro ao desligar fonte: {exc}")

        if was_measuring and self.readings:
            self.alert_label.setText("Voltametria finalizada. Fonte desligada.")

    # ------------------------------------------------------------------
    # Configuração
    # ------------------------------------------------------------------

    def configure_instrument_step(self, step):
        if not self.measuring or self.instrument is None:
            return

        commands = [
            "*RST",
            "FORM:ELEM READ,VSO",
            "SYST:ZCH ON",
            f"SENS:CURR:NPLC {self.nplc_spin.value()}",
            f"SOUR:VOLT:ILIM {self.ilim_spin.value()}",
            "SOUR:VOLT:STAT ON",
            "SYST:ZCH OFF",
        ]

        try:
            if step < len(commands):
                self.instrument.write(commands[step])
                QTimer.singleShot(200, lambda: self.configure_instrument_step(step + 1))
                return

            self.instrument.write(f"SOUR:VOLT {self.v_current}")
            QTimer.singleShot(max(50, int(self.interval * 1000)), self.acquire_reading)

        except Exception as exc:
            self.alert_label.setText(f"Erro na configuração: {exc}")
            self.stop_measurement()

    # ------------------------------------------------------------------
    # Aquisição e Lógica de Varredura
    # ------------------------------------------------------------------

    def acquire_reading(self):
        if not self.measuring or self.instrument is None:
            return

        try:
            response = self.instrument.query("READ?")
            values = [float(v.strip()) for v in response.strip().split(",")]

            if len(values) < 2:
                raise ValueError(f"Resposta inesperada do 6487: {response!r}")

            current, voltage = values[0], values[1]

            if abs(current) > self.ilim_spin.value():
                self.alert_label.setText("Limite de corrente excedido! Medição interrompida.")
                self.stop_measurement()
                return

            if self.first_reading_time is None:
                self.first_reading_time = datetime.now()
                relative_time = 0.0
            else:
                relative_time = (datetime.now() - self.first_reading_time).total_seconds()

            self.readings.append((relative_time, voltage, current, self.phase, self.cycle_count + 1))
            self.update_display()

            if self._advance_voltage():
                self.measure_timer.start(int(self.interval * 1000))
            else:
                self._change_phase_or_cycle()

        except Exception as exc:
            self.alert_label.setText(f"Erro ao adquirir leitura: {exc}")
            self.stop_measurement()

    def _advance_voltage(self):
        next_voltage = self.v_current + (self.step_value * self.direction)

        if self.phase == "IDA":
            if (self.direction > 0 and next_voltage >= self.v2_value) or \
                    (self.direction < 0 and next_voltage <= self.v2_value):
                self.v_current = self.v2_value
                return False
        elif self.phase == "VOLTA":
            if (self.direction > 0 and next_voltage >= self.v1_value) or \
                    (self.direction < 0 and next_voltage <= self.v1_value):
                self.v_current = self.v1_value
                return False

        self.v_current = next_voltage

        try:
            self.instrument.write(f"SOUR:VOLT {self.v_current}")
        except Exception as exc:
            self.alert_label.setText(f"Erro ao aplicar tensão: {exc}")
            self.stop_measurement()
            return False

        return True

    def _change_phase_or_cycle(self):
        try:
            self.instrument.write(f"SOUR:VOLT {self.v_current}")

            if self.phase == "IDA":
                self.phase = "VOLTA"
                self.direction *= -1  # Inverte a direção
                self.measure_timer.start(int(self.interval * 1000))
            else:
                self.cycle_count += 1
                if self.cycle_count >= self.max_cycles:
                    self.stop_measurement()
                else:
                    self.phase = "IDA"
                    self.direction *= -1  # Inverte a direção de volta para a original
                    self.measure_timer.start(int(self.interval * 1000))
        except Exception as exc:
            self.alert_label.setText(f"Erro ao mudar fase: {exc}")
            self.stop_measurement()

    # ------------------------------------------------------------------
    # Display e Persistência
    # ------------------------------------------------------------------

    def update_display(self):
        if not self.readings:
            return

        t, voltage, current, phase, cycle = self.readings[-1]

        self.list_widget.addItem(
            f"Ciclo {cycle} | {phase} | V = {self.format_number(voltage)} V | I = {self.format_number(current)} A"
        )
        self.list_widget.scrollToBottom()

        elapsed_str = str(timedelta(seconds=int(t)))
        self.stats_label.setText(f"Ciclos: {cycle}/{self.max_cycles} | Tempo: {elapsed_str} | Fase: {phase}")

        voltages = [r[1] for r in self.readings]
        currents = [r[2] for r in self.readings]
        self.cv_curve.setData(voltages, currents)

        self.auto_save_reading(t, voltage, current, phase, cycle)

    def auto_save_reading(self, time, voltage, current, phase, cycle):
        if not self.temp_file_path:
            return
        try:
            if not os.path.exists(self.temp_file_path):
                with open(self.temp_file_path, "w", encoding="utf-8") as f:
                    f.write("# Auto-save - Voltametria Cíclica (Pico 6487)\n")
                    f.write(f"# V1: {self.v1_spin.value()} V | V2: {self.v2_spin.value()} V\n")
                    f.write(f"# Passo: {self.step_spin.value()} V | Taxa: {self.scan_rate_spin.value()} V/s\n")
                    f.write("Tempo_(s)\tTensao_(V)\tCorrente_(A)\tFase\tCiclo\n")

            with open(self.temp_file_path, "a", encoding="utf-8") as f:
                f.write(f"{time:.3f}\t{voltage:.6e}\t{current:.6e}\t{phase}\t{cycle}\n")
        except Exception as exc:
            print(f"Erro ao salvar: {exc}")

    def export_measurement(self):
        if not self.readings:
            QMessageBox.warning(self, "Aviso", "Nenhuma leitura para exportar.")
            return

        default_filename = f"cv_6487_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"

        path = self._last_export_dir if self._last_export_dir else ""
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar Medição", os.path.join(path, default_filename),
                                                  "Text Files (*.txt)")

        if not filename:
            return

        self._last_export_dir = os.path.dirname(filename)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# Voltametria Cíclica - Keithley 6487\n")
                f.write(f"# V1 (V): {self.v1_spin.value()}\n")
                f.write(f"# V2 (V): {self.v2_spin.value()}\n")
                f.write(f"# Passo (V): {self.step_spin.value()}\n")
                f.write(f"# Taxa de Varredura (V/s): {self.scan_rate_spin.value()}\n")
                f.write(f"# Ciclos: {self.cycles_spin.value()}\n")
                f.write("Tempo_(s)\tTensao_(V)\tCorrente_(A)\tFase\tCiclo\n")

                for t, voltage, current, phase, cycle in self.readings:
                    f.write(f"{t:.3f}\t{voltage:.6e}\t{current:.6e}\t{phase}\t{cycle}\n")

            QMessageBox.information(self, "Sucesso", f"Exportado para:\n{filename}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro na exportação: {exc}")

    def load_measurement(self):
        # Implementação básica de load de dados exportados
        pass

    def save_parameters(self):
        # Implementação análoga aos blocos existentes para salvar JSON
        pass

    def load_parameters(self):
        # Implementação análoga aos blocos existentes para carregar JSON
        pass

    @staticmethod
    def format_number(value):
        if abs(value) >= 1:
            return f"{value:.6f}".rstrip("0").rstrip(".")
        formatted = f"{value:.6e}"
        mantissa, exponent = formatted.split("e")
        return f"{mantissa.rstrip('0').rstrip('.')}e{exponent}"