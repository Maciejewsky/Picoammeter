# widgets/pico_6487/block_charge_discharge.py
#
# Medição de carga e descarga de capacitor no domínio do tempo (Cronoamperometria) com o Keithley 6487.
#
# O procedimento:
# - configura a fonte e o amperímetro;
# - Fase de Carga: aplica a Tensão de Carga configurada e mantém pelo Tempo de Carga;
# - Fase de Descarga (opcional): zera a tensão (0.0 V) mantendo a fonte ligada e aguarda o Tempo de Descarga;
# - executa READ? e registra corrente/tensão continuadamente de acordo com o intervalo;
# - salva automaticamente os pontos em arquivo temporário;
# - permite exportar a medição completa.
#
# IMPORTANTE:
# Este bloco implementa uma carga/descarga baseada em tempo.
# O circuito externo deve fornecer o caminho elétrico apropriado
# para a descarga.

from datetime import datetime, timedelta
import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg


class ChargeDischargeBlock(QWidget):
    _last_params_dir = None
    _last_export_dir = None
    _last_load_dir = None

    def __init__(self, instrument, user_manager=None, parent=None):
        super().__init__(parent)

        self.instrument = instrument
        self.user_manager = user_manager

        self.measuring = False
        self.phase = "CARGA"
        self.readings = []
        self.first_reading_time = None
        self.start_time = None
        self.temp_file_path = None

        self.v_current = 0.0
        self.v_charge_value = 0.0
        self.t_charge_value = 0.0
        self.t_discharge_value = 0.0
        self.phase_start_time = None

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

        params_group = QGroupBox("Parâmetros de Carga / Descarga")
        params_layout = QVBoxLayout()

        self.v_charge_spin = self._create_voltage_spin(10.0)
        self._add_row(params_layout, "Tensão de Carga (V):", self.v_charge_spin)

        self.t_charge_spin = QDoubleSpinBox()
        self.t_charge_spin.setRange(0.1, 100000.0)
        self.t_charge_spin.setDecimals(1)
        self.t_charge_spin.setValue(10.0)
        self._add_row(params_layout, "Tempo de Carga (s):", self.t_charge_spin)

        self.t_discharge_spin = QDoubleSpinBox()
        self.t_discharge_spin.setRange(0.1, 100000.0)
        self.t_discharge_spin.setDecimals(1)
        self.t_discharge_spin.setValue(10.0)
        self._add_row(params_layout, "Tempo de Descarga (s):", self.t_discharge_spin)

        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(2.5e-6, 2.5e-2)
        self.ilim_spin.setDecimals(6)
        self.ilim_spin.setValue(0.025)
        self.ilim_spin.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self._add_row(params_layout, "Limite de corrente (A):", self.ilim_spin)

        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.1, 6.0)
        self.nplc_spin.setDecimals(1)
        self.nplc_spin.setValue(1.0)
        self._add_row(params_layout, "NPLC:", self.nplc_spin)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 60.0)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setValue(0.5)
        self._add_row(params_layout, "Intervalo (s):", self.interval_spin)

        self.charge_checkbox = QCheckBox("Executar carga")
        self.charge_checkbox.setChecked(True)
        params_layout.addWidget(self.charge_checkbox)

        self.discharge_checkbox = QCheckBox("Executar descarga")
        self.discharge_checkbox.setChecked(True)
        params_layout.addWidget(self.discharge_checkbox)

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

        self.toggle_button = QPushButton("Iniciar Carga / Descarga")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_measurement)
        left_layout.addWidget(self.toggle_button)

        self.list_widget = QListWidget()
        left_layout.addWidget(self.list_widget)

        self.stats_label = QLabel(
            "Total de leituras: 0 | Tempo: 00:00:00 | Fase: --"
        )
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

        # Gráfico 1: tensão aplicada x tempo
        self.voltage_plot = pg.PlotWidget(title="Tensão x Tempo")
        self.voltage_plot.setLabel("left", "Tensão (V)")
        self.voltage_plot.setLabel("bottom", "Tempo (s)")
        self.voltage_curve = self.voltage_plot.plot(
            [], [], pen=pg.mkPen(color="r", width=2)
        )

        # Gráfico 2: corrente x tempo
        self.current_plot = pg.PlotWidget(title="Corrente x Tempo")
        self.current_plot.setLabel("left", "Corrente (A)")
        self.current_plot.setLabel("bottom", "Tempo (s)")
        self.current_curve = self.current_plot.plot(
            [], [], pen=pg.mkPen(color="b", width=2)
        )

        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(self.voltage_plot)
        graph_layout.addWidget(self.current_plot)

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
            self.toggle_button.blockSignals(True)
            self.toggle_button.setChecked(False)
            self.toggle_button.blockSignals(False)
            return

        v_charge = self.v_charge_spin.value()
        t_charge = self.t_charge_spin.value()
        t_discharge = self.t_discharge_spin.value()

        if not self.charge_checkbox.isChecked() and not self.discharge_checkbox.isChecked():
            QMessageBox.warning(
                self,
                "Parâmetros inválidos",
                "Selecione pelo menos Carga ou Descarga."
            )
            self._reset_toggle()
            return

        self.measuring = True
        self.phase = "CARGA" if self.charge_checkbox.isChecked() else "DESCARGA"

        self.readings.clear()
        self.list_widget.clear()
        self.alert_label.setText("")
        self.first_reading_time = None
        self.start_time = datetime.now()

        self.v_charge_value = v_charge
        self.t_charge_value = t_charge
        self.t_discharge_value = t_discharge
        self.phase_start_time = None

        self.voltage_curve.setData([], [])
        self.current_curve.setData([], [])

        self.toggle_button.setText("Parar Medição")

        if self.user_manager:
            try:
                temp_dir = self.user_manager.get_user_directory(
                    "measurements/charge_discharge"
                )
                timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
                self.temp_file_path = (
                    temp_dir / f"temp_charge_discharge_6487_{timestamp}.txt"
                )
            except Exception:
                self.temp_file_path = None
        else:
            self.temp_file_path = None

        self.configure_instrument_step(0)

    def _reset_toggle(self):
        self.toggle_button.blockSignals(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.blockSignals(False)
        self.toggle_button.setText("Iniciar Carga / Descarga")

    def stop_measurement(self):
        was_measuring = self.measuring
        self.measuring = False
        self.measure_timer.stop()

        self.toggle_button.blockSignals(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.blockSignals(False)
        self.toggle_button.setText("Iniciar Carga / Descarga")

        if self.instrument is not None:
            try:
                self.instrument.write("SOUR:VOLT:STAT OFF")
            except Exception as exc:
                print(f"Erro ao desligar fonte: {exc}")

        if was_measuring and self.readings:
            self.alert_label.setText(
                "Medição finalizada. Fonte desligada."
            )

    # ------------------------------------------------------------------
    # Configuração sequencial do 6487
    # ------------------------------------------------------------------

    def configure_instrument_step(self, step):
        if not self.measuring or self.instrument is None:
            return

        nplc = self.nplc_spin.value()
        i_limit = self.ilim_spin.value()

        commands = [
            "*RST",
            "FORM:ELEM READ,VSO",
            "SYST:ZCH ON",
            f"SENS:CURR:NPLC {nplc}",
            f"SOUR:VOLT:ILIM {i_limit}",
            "SOUR:VOLT:STAT ON",
            "SYST:ZCH OFF",
        ]

        try:
            if step < len(commands):
                self.instrument.write(commands[step])
                QTimer.singleShot(
                    200,
                    lambda: self.configure_instrument_step(step + 1)
                )
                return

            self.v_current = (
                self.v_charge_value
                if self.phase == "CARGA"
                else 0.0
            )

            self.instrument.write(f"SOUR:VOLT {self.v_current}")

            # Dá tempo para a fonte estabilizar antes da primeira leitura.
            QTimer.singleShot(
                max(50, int(self.interval_spin.value() * 1000)),
                self.acquire_reading
            )

        except Exception as exc:
            self.alert_label.setText(
                f"Erro na configuração do instrumento: {exc}"
            )
            self.stop_measurement()

    # ------------------------------------------------------------------
    # Aquisição
    # ------------------------------------------------------------------

    def acquire_reading(self):
        if not self.measuring or self.instrument is None:
            return

        try:
            response = self.instrument.query("READ?")
            values = [float(v.strip()) for v in response.strip().split(",")]

            if len(values) < 2:
                raise ValueError(
                    f"Resposta inesperada do 6487: {response!r}"
                )

            current = values[0]
            voltage = values[1]

            i_limit = self.ilim_spin.value()

            if abs(current) > i_limit:
                self.alert_label.setText(
                    "Limite de corrente excedido! Medição interrompida."
                )
                self.stop_measurement()
                return

            now = datetime.now()
            if self.first_reading_time is None:
                self.first_reading_time = now
                self.phase_start_time = now
                relative_time = 0.0
            else:
                relative_time = (
                    now - self.first_reading_time
                ).total_seconds()

            # t, corrente, tensão, fase
            self.readings.append(
                (relative_time, current, voltage, self.phase)
            )

            self.update_display()

            phase_elapsed = (now - self.phase_start_time).total_seconds()

            if self.phase == "CARGA":
                if phase_elapsed >= self.t_charge_value:
                    if self.discharge_checkbox.isChecked():
                        # Transição para descarga
                        self.phase = "DESCARGA"
                        self.phase_start_time = now
                        self.v_current = 0.0
                        try:
                            self.instrument.write(f"SOUR:VOLT {self.v_current}")
                        except Exception as exc:
                            self.alert_label.setText(f"Erro ao aplicar tensão 0.0V: {exc}")
                            self.stop_measurement()
                            return
                    else:
                        # Acabou teste sem descarga
                        self.stop_measurement()
                        return
            elif self.phase == "DESCARGA":
                if phase_elapsed >= self.t_discharge_value:
                    self.stop_measurement()
                    return

            # Continua medindo se não chamou stop_measurement
            self.measure_timer.start(
                int(self.interval_spin.value() * 1000)
            )

        except Exception as exc:
            self.alert_label.setText(
                f"Erro ao adquirir leitura: {exc}"
            )
            self.stop_measurement()

    # ------------------------------------------------------------------
    # Display / autosave
    # ------------------------------------------------------------------

    def update_display(self):
        if not self.readings:
            return

        t, current, voltage, phase = self.readings[-1]

        self.list_widget.addItem(
            f"{t:.2f} s | {phase} | "
            f"I = {self.format_number(current)} A | "
            f"V = {self.format_number(voltage)} V"
        )
        self.list_widget.scrollToBottom()

        elapsed_str = str(timedelta(seconds=int(t)))
        self.stats_label.setText(
            f"Total de leituras: {len(self.readings)} | "
            f"Tempo: {elapsed_str} | Fase: {phase}"
        )

        times = [r[0] for r in self.readings]
        currents = [r[1] for r in self.readings]
        voltages = [r[2] for r in self.readings]

        self.voltage_curve.setData(times, voltages)
        self.current_curve.setData(times, currents)

        self.auto_save_reading(t, current, voltage, phase)

    def auto_save_reading(self, time, current, voltage, phase):
        if not self.temp_file_path:
            return

        try:
            if not os.path.exists(self.temp_file_path):
                with open(self.temp_file_path, "w", encoding="utf-8") as f:
                    f.write(
                        "# Auto-save temporário - "
                        "Carga/Descarga de Capacitor (Pico 6487)\n"
                    )
                    f.write(f"# Início: {self.start_time}\n")
                    f.write(
                        f"# Tensão de Carga (V): {self.v_charge_spin.value()}\n"
                    )
                    f.write(
                        f"# Tempo de Carga (s): {self.t_charge_spin.value()}\n"
                    )
                    f.write(
                        f"# Tempo de Descarga (s): {self.t_discharge_spin.value()}\n"
                    )
                    f.write(
                        "# Limite corrente (A): "
                        f"{self.format_number(self.ilim_spin.value())}\n"
                    )
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(
                        f"# Intervalo (s): {self.interval_spin.value()}\n"
                    )
                    f.write(
                        f"# Executar carga: "
                        f"{self.charge_checkbox.isChecked()}\n"
                    )
                    f.write(
                        f"# Executar descarga: "
                        f"{self.discharge_checkbox.isChecked()}\n"
                    )
                    f.write(
                        "Tempo_(s)\tCorrente_(A)\tTensao_(V)\tFase\n"
                    )

            with open(self.temp_file_path, "a", encoding="utf-8") as f:
                f.write(
                    f"{time:.3f}\t{current:.6e}\t"
                    f"{voltage:.6e}\t{phase}\n"
                )

        except Exception as exc:
            print(f"Erro ao salvar temporariamente: {exc}")

    # ------------------------------------------------------------------
    # Parâmetros
    # ------------------------------------------------------------------

    def save_parameters(self):
        if not self.user_manager:
            QMessageBox.warning(
                self,
                "Erro",
                "Sistema de usuários não disponível"
            )
            return

        if self._last_params_dir:
            start_dir = self._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory(
                "configs/presets"
            )
            start_dir = str(params_dir)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Parâmetros",
            start_dir,
            "JSON Files (*.json)"
        )

        if not filename:
            return

        self._last_params_dir = os.path.dirname(filename)

        parameters = {
            "measurement_type": "charge_discharge",
            "instrument_type": "pico_6487",
            "v_charge": self.v_charge_spin.value(),
            "t_charge": self.t_charge_spin.value(),
            "t_discharge": self.t_discharge_spin.value(),
            "current_limit": self.ilim_spin.value(),
            "nplc": self.nplc_spin.value(),
            "interval": self.interval_spin.value(),
            "charge": self.charge_checkbox.isChecked(),
            "discharge": self.discharge_checkbox.isChecked(),
            "saved_at": datetime.now().isoformat(),
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(parameters, f, indent=2)

            QMessageBox.information(
                self,
                "Sucesso",
                "Parâmetros salvos com sucesso!"
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao salvar parâmetros: {exc}"
            )

    def load_parameters(self):
        if not self.user_manager:
            QMessageBox.warning(
                self,
                "Erro",
                "Sistema de usuários não disponível"
            )
            return

        if self._last_params_dir:
            start_dir = self._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory(
                "configs/presets"
            )
            start_dir = str(params_dir)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Parâmetros",
            start_dir,
            "JSON Files (*.json)"
        )

        if not filename:
            return

        self._last_params_dir = os.path.dirname(filename)

        try:
            with open(filename, "r", encoding="utf-8") as f:
                parameters = json.load(f)

            if parameters.get("measurement_type") != "charge_discharge":
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Arquivo não é de carga/descarga."
                )
                return

            self.v_charge_spin.setValue(
                parameters.get("v_charge", 10.0)
            )
            self.t_charge_spin.setValue(
                parameters.get("t_charge", 10.0)
            )
            self.t_discharge_spin.setValue(
                parameters.get("t_discharge", 10.0)
            )
            self.ilim_spin.setValue(
                parameters.get("current_limit", 0.025)
            )
            self.nplc_spin.setValue(
                parameters.get("nplc", 1.0)
            )
            self.interval_spin.setValue(
                parameters.get("interval", 0.5)
            )
            self.charge_checkbox.setChecked(
                parameters.get("charge", True)
            )
            self.discharge_checkbox.setChecked(
                parameters.get("discharge", True)
            )

            QMessageBox.information(
                self,
                "Sucesso",
                "Parâmetros carregados com sucesso!"
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar parâmetros: {exc}"
            )

    # ------------------------------------------------------------------
    # Exportação
    # ------------------------------------------------------------------

    def export_measurement(self):
        if not self.readings:
            QMessageBox.warning(
                self,
                "Aviso",
                "Nenhuma leitura para exportar."
            )
            return

        default_filename = (
            f"charge_discharge_6487_"
            f"{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if self._last_export_dir:
            default_path = os.path.join(
                self._last_export_dir,
                default_filename
            )
        elif self.user_manager:
            export_dir = self.user_manager.get_user_directory("exports")
            default_path = str(export_dir / default_filename)
        else:
            default_path = default_filename

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Medição",
            default_path,
            "Text Files (*.txt)"
        )

        if not filename:
            return

        self._last_export_dir = os.path.dirname(filename)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(
                    "# Keithley LabNano3D - "
                    "Carga/Descarga de Capacitor\n"
                )

                if self.user_manager:
                    try:
                        user_info = self.user_manager.get_current_user_info()
                        user_name = (
                            f"{user_info.get('first_name', '')} "
                            f"{user_info.get('last_name', '')}"
                        ).strip()
                        f.write(f"# Usuário: {user_name}\n")
                    except Exception:
                        pass

                f.write("# Equipamento: Picoammeter 6487\n")
                f.write(f"# Data início: {self.start_time}\n")

                if self.first_reading_time:
                    f.write(
                        f"# Primeira leitura: "
                        f"{self.first_reading_time}\n"
                    )

                f.write(f"# Data fim: {datetime.now()}\n")
                f.write("#\n")
                f.write("# Parâmetros:\n")
                f.write(
                    f"# Tensão de Carga (V): "
                    f"{self.v_charge_spin.value()}\n"
                )
                f.write(
                    f"# Tempo de Carga (s): "
                    f"{self.t_charge_spin.value()}\n"
                )
                f.write(
                    f"# Tempo de Descarga (s): "
                    f"{self.t_discharge_spin.value()}\n"
                )
                f.write(
                    "# Limite corrente (A): "
                    f"{self.format_number(self.ilim_spin.value())}\n"
                )
                f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                f.write(
                    f"# Intervalo (s): "
                    f"{self.interval_spin.value()}\n"
                )
                f.write(
                    f"# Carga: "
                    f"{self.charge_checkbox.isChecked()}\n"
                )
                f.write(
                    f"# Descarga: "
                    f"{self.discharge_checkbox.isChecked()}\n"
                )
                f.write(
                    f"# Número de leituras: {len(self.readings)}\n"
                )
                f.write(
                    f"# Tempo total: "
                    f"{datetime.now() - self.start_time}\n"
                )
                f.write("# ---\n")
                f.write(
                    "Tempo_(s)\tCorrente_(A)\t"
                    "Tensao_(V)\tFase\n"
                )

                for t, current, voltage, phase in self.readings:
                    f.write(
                        f"{t:.3f}\t{current:.6e}\t"
                        f"{voltage:.6e}\t{phase}\n"
                    )

            QMessageBox.information(
                self,
                "Sucesso",
                f"Medição exportada para:\n{filename}"
            )

            if self.temp_file_path and os.path.exists(self.temp_file_path):
                try:
                    os.remove(self.temp_file_path)
                except OSError:
                    pass

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao exportar medição: {exc}"
            )

    # ------------------------------------------------------------------
    # Carregar medição
    # ------------------------------------------------------------------

    def load_measurement(self):
        if self._last_load_dir:
            start_dir = self._last_load_dir
        elif self.user_manager:
            measurements_dir = self.user_manager.get_user_directory(
                "exports"
            )
            start_dir = str(measurements_dir)
        else:
            start_dir = ""

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Medição",
            start_dir,
            "Text Files (*.txt)"
        )

        if not filename:
            return

        self._last_load_dir = os.path.dirname(filename)

        try:
            readings = []

            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or line.startswith("Tempo"):
                        continue

                    parts = line.strip().split("\t")

                    if len(parts) >= 4:
                        try:
                            t = float(parts[0])
                            current = float(parts[1])
                            voltage = float(parts[2])
                            phase = parts[3]
                            readings.append(
                                (t, current, voltage, phase)
                            )
                        except ValueError:
                            continue

                    # Compatibilidade com arquivo sem coluna Fase.
                    elif len(parts) >= 3:
                        try:
                            t = float(parts[0])
                            current = float(parts[1])
                            voltage = float(parts[2])
                            readings.append(
                                (t, current, voltage, "N/D")
                            )
                        except ValueError:
                            continue

            if not readings:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Nenhum dado válido encontrado no arquivo."
                )
                return

            self.readings = readings
            self.list_widget.clear()

            for t, current, voltage, phase in readings:
                self.list_widget.addItem(
                    f"{t:.2f} s | {phase} | "
                    f"I = {self.format_number(current)} A | "
                    f"V = {self.format_number(voltage)} V"
                )

            times = [r[0] for r in readings]
            currents = [r[1] for r in readings]
            voltages = [r[2] for r in readings]

            self.voltage_curve.setData(times, voltages)
            self.current_curve.setData(times, currents)

            elapsed_str = str(
                timedelta(seconds=int(readings[-1][0]))
            )
            self.stats_label.setText(
                f"Total de leituras: {len(readings)} | "
                f"Tempo: {elapsed_str} (Carregada)"
            )

            QMessageBox.information(
                self,
                "Sucesso",
                f"Medição carregada: {len(readings)} pontos"
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar medição: {exc}"
            )

    # ------------------------------------------------------------------
    # Utilitário
    # ------------------------------------------------------------------

    @staticmethod
    def format_number(value):
        if abs(value) >= 1:
            return f"{value:.6f}".rstrip("0").rstrip(".")

        formatted = f"{value:.6e}"
        mantissa, exponent = formatted.split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa}e{exponent}"
