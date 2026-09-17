# widgets/smu_2450/block_iv_measurement.py

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QComboBox, QCheckBox,
    QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import json
import os

class IVMeasurementBlock(QWidget):
    # Class variables to remember last used directories
    _last_params_dir = None
    _last_export_dir = None
    _last_load_dir = None
    
    def __init__(self, instrument, user_manager=None, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.user_manager = user_manager
        self.measuring = False
        self.readings = []
        self.start_time = None
        self.first_reading_time = None
        self.last_buffer_index = 0  # índice do último ponto lido
        self.temp_file_path = None  # Path to temporary save file

        self.measure_timer = QTimer()
        self.measure_timer.timeout.connect(self.acquire_buffer_readings)

        splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)

        # ----- Controles e leituras (esquerda) -----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Parameters group
        params_group = QGroupBox("Parâmetros de Medição")
        params_layout = QVBoxLayout()

        # V start
        hlayout_start = QHBoxLayout()
        hlayout_start.addWidget(QLabel("V start (V):"))
        self.v_start_spin = QDoubleSpinBox()
        self.v_start_spin.setRange(-210, 210)
        self.v_start_spin.setDecimals(3)
        self.v_start_spin.setValue(0.0)
        hlayout_start.addWidget(self.v_start_spin)
        params_layout.addLayout(hlayout_start)

        # V stop
        hlayout_stop = QHBoxLayout()
        hlayout_stop.addWidget(QLabel("V stop (V):"))
        self.v_stop_spin = QDoubleSpinBox()
        self.v_stop_spin.setRange(-210, 210)
        self.v_stop_spin.setDecimals(3)
        self.v_stop_spin.setValue(5.0)
        hlayout_stop.addWidget(self.v_stop_spin)
        params_layout.addLayout(hlayout_stop)

        # Step
        hlayout_step = QHBoxLayout()
        hlayout_step.addWidget(QLabel("Step (V):"))
        self.v_step_spin = QDoubleSpinBox()
        self.v_step_spin.setRange(0.001, 10)
        self.v_step_spin.setDecimals(3)
        self.v_step_spin.setValue(0.1)
        hlayout_step.addWidget(self.v_step_spin)
        params_layout.addLayout(hlayout_step)

        # Delay
        hlayout_delay = QHBoxLayout()
        hlayout_delay.addWidget(QLabel("Delay (s):"))
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 10.0)
        self.delay_spin.setDecimals(3)
        self.delay_spin.setValue(0.05)
        hlayout_delay.addWidget(self.delay_spin)
        params_layout.addLayout(hlayout_delay)

        # Limite de corrente - with improved formatting
        hlayout_ilim = QHBoxLayout()
        hlayout_ilim.addWidget(QLabel("Limite de corrente (A):"))
        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(1e-9, 1.0)
        self.ilim_spin.setDecimals(9)
        self.ilim_spin.setValue(1e-3)
        self.ilim_spin.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        hlayout_ilim.addWidget(self.ilim_spin)
        params_layout.addLayout(hlayout_ilim)

        # NPLC
        hlayout_nplc = QHBoxLayout()
        hlayout_nplc.addWidget(QLabel("NPLC:"))
        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.01, 10.0)
        self.nplc_spin.setDecimals(2)
        self.nplc_spin.setValue(1.0)
        hlayout_nplc.addWidget(self.nplc_spin)
        params_layout.addLayout(hlayout_nplc)

        # Count
        hlayout_count = QHBoxLayout()
        hlayout_count.addWidget(QLabel("Count:"))
        self.count_spin = QDoubleSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setDecimals(0)
        self.count_spin.setValue(1)
        hlayout_count.addWidget(self.count_spin)
        params_layout.addLayout(hlayout_count)

        # Dual checkbox
        hlayout_dual = QHBoxLayout()
        self.dual_checkbox = QCheckBox("Dual sweep")
        hlayout_dual.addWidget(self.dual_checkbox)
        params_layout.addLayout(hlayout_dual)
        
        # Save/Load parameter buttons
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

        # Botão iniciar/parar
        self.toggle_button = QPushButton("Iniciar Sweep")
        self.toggle_button.clicked.connect(self.toggle_measurement)
        left_layout.addWidget(self.toggle_button)

        # Lista de leituras
        self.list_widget = QListWidget()
        left_layout.addWidget(self.list_widget)

        # Estatísticas
        self.stats_label = QLabel("Total de leituras: 0 | Tempo: 00:00:00")
        left_layout.addWidget(self.stats_label)

        # Mensagem de alerta
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: red; font-weight: bold;")
        left_layout.addWidget(self.alert_label)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        # Botão exportar medição (anteriormente "Salvar leituras")
        self.export_button = QPushButton("Exportar Medição")
        self.export_button.clicked.connect(self.export_measurement)
        buttons_layout.addWidget(self.export_button)
        
        # Botão carregar medição
        load_measurement_btn = QPushButton("Carregar Medição")
        load_measurement_btn.clicked.connect(self.load_measurement)
        buttons_layout.addWidget(load_measurement_btn)
        
        left_layout.addLayout(buttons_layout)

        splitter.addWidget(left_widget)

        # ----- Gráfico I-V (direita) -----
        self.plot_widget = pg.PlotWidget(title="I-V")
        self.plot_widget.setLabel('left', 'Corrente (A)')
        self.plot_widget.setLabel('bottom', 'Tensão (V)')
        self.curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='r', width=2))
        splitter.addWidget(self.plot_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    # ----- Controle da medição -----
    def toggle_measurement(self):
        if self.measuring:
            self.stop_measurement()
        else:
            self.start_measurement()

    def start_measurement(self):
        self.measuring = True
        self.readings.clear()
        self.list_widget.clear()
        self.alert_label.setText("")
        self.start_time = datetime.now()
        self.first_reading_time = None
        self.last_buffer_index = 0
        self.toggle_button.setText("Parar Sweep")
        self.curve.setData([], [])
        
        # Create temporary file for auto-save
        if self.user_manager:
            temp_dir = self.user_manager.get_user_directory("measurements/iv")
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            self.temp_file_path = temp_dir / f"temp_iv_{timestamp}.txt"
        else:
            self.temp_file_path = None

        v_start = self.v_start_spin.value()
        v_stop = self.v_stop_spin.value()
        v_step = self.v_step_spin.value()
        s_delay = self.delay_spin.value()
        count = int(self.count_spin.value())
        dual = "smu.ON" if self.dual_checkbox.isChecked() else "smu.OFF"

        config_list_name = "VoltageSweepStepConfig"

        try:
            # Reset e configuração inicial
            self.instrument.write("reset()")
            self.instrument.write("smu.source.func = smu.FUNC_DC_VOLTAGE")
            self.instrument.write(f"smu.source.ilimit.level = {self.ilim_spin.value()}")
            self.instrument.write("smu.measure.func = smu.FUNC_DC_CURRENT")
            self.instrument.write("smu.measure.unit = smu.UNIT_AMP")
            self.instrument.write("smu.measure.terminals = smu.TERMINALS_FRONT")
            self.instrument.write("smu.measure.autorange = smu.ON")
            self.instrument.write(f"smu.measure.nplc = {self.nplc_spin.value()}")

            # Configura trigger e buffer
            self.instrument.write(f"trigger.model.setblock(1, trigger.BLOCK_BUFFER_CLEAR, defbuffer1)")
            self.instrument.write(f"smu.source.configlist.create('{config_list_name}')")
            sweep_cmd = (
                f"smu.source.sweeplinearstep('{config_list_name}', {v_start}, {v_stop}, {v_step}, "
                f"{s_delay}, {count}, smu.RANGE_BEST, smu.OFF, {dual})"
            )
            self.instrument.write(sweep_cmd)

            # Liga saída e inicia trigger
            self.instrument.write("smu.source.output = smu.ON")
            self.instrument.write("trigger.model.initiate()")

            # Inicia timer para ler buffer
            self.measure_timer.start(100)

        except Exception as e:
            print(f"Erro ao iniciar sweep: {e}")
            self.stop_measurement()

    def stop_measurement(self):
        self.measuring = False
        self.measure_timer.stop()
        self.toggle_button.setText("Iniciar Sweep")
        if self.instrument:
            try:
                self.instrument.write("smu.source.output = smu.OFF")
            except Exception as e:
                print(f"Erro ao desligar fonte: {e}")

    def acquire_buffer_readings(self):
        if not self.measuring or self.instrument is None:
            return
        try:
            # Pega o número de leituras no buffer
            resp = self.instrument.query("print(defbuffer1.n)").strip()
            num_readings = int(resp)
            if num_readings <= self.last_buffer_index:
                return

            # Lê os novos pontos
            for i in range(self.last_buffer_index + 1, num_readings + 1):
                # defbuffer1.sourcevalues[i] = tensão aplicada
                # defbuffer1[i] = corrente medida
                resp_voltage = self.instrument.query(f"print(defbuffer1.sourcevalues[{i}])").strip()
                resp_current = self.instrument.query(f"print(defbuffer1[{i}])").strip()
                voltage = float(resp_voltage)
                current = float(resp_current)

                if abs(current) > self.ilim_spin.value():
                    self.alert_label.setText("Limite de corrente excedido!")
                    self.stop_measurement()
                    return

                relative_time = (datetime.now() - self.start_time).total_seconds()
                self.readings.append((relative_time, current, voltage))

            self.last_buffer_index = num_readings
            self.update_display()

            # Verifica se trigger finalizou
            resp_done = self.instrument.query("print(trigger.model.state())").strip()
            if resp_done == "trigger.STATE_IDLE	trigger.STATE_IDLE	10":  # STATE_IDLE
                self.stop_measurement()

        except Exception as e:
            print(f"Erro ao ler buffer: {e}")
            self.stop_measurement()

    def update_display(self):
        self.list_widget.clear()
        for t, current, voltage in self.readings:
            # Use formatted numbers for display
            self.list_widget.addItem(
                f"{t:.2f} s | I = {self.format_number(current)} A | V = {self.format_number(voltage)} V"
            )
        self.list_widget.scrollToBottom()

        if self.readings:
            elapsed_str = str(timedelta(seconds=int(self.readings[-1][0])))
            self.stats_label.setText(f"Total de leituras: {len(self.readings)} | Tempo: {elapsed_str}")

            x = [r[2] for r in self.readings]
            y = [r[1] for r in self.readings]
            self.curve.setData(x, y)
            
            # Auto-save last reading
            if len(self.readings) > 0:
                t, i, v = self.readings[-1]
                self.auto_save_reading(t, i, v)
    
    def auto_save_reading(self, time, current, voltage):
        """Auto-save reading to temporary file"""
        if not self.temp_file_path:
            return
        
        try:
            # Create file with header if it doesn't exist
            if not os.path.exists(self.temp_file_path):
                if self.first_reading_time is None:
                    self.first_reading_time = datetime.now()
                    
                with open(self.temp_file_path, 'w') as f:
                    f.write(f"# Auto-save temporário - Medição I-V\n")
                    f.write(f"# Início: {self.start_time}\n")
                    f.write(f"# V start (V): {self.v_start_spin.value()}\n")
                    f.write(f"# V stop (V): {self.v_stop_spin.value()}\n")
                    f.write(f"# Step (V): {self.v_step_spin.value()}\n")
                    f.write(f"# Delay (s): {self.delay_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Count: {int(self.count_spin.value())}\n")
                    f.write(f"# Dual sweep: {self.dual_checkbox.isChecked()}\n")
                    f.write("Tempo_(s)\tCorrente_(A)\tTensao_(V)\n")
            
            # Append reading
            with open(self.temp_file_path, 'a') as f:
                f.write(f"{time:.2f}\t{current:.6e}\t{voltage:.6e}\n")
        except Exception as e:
            print(f"Erro ao salvar temporariamente: {e}")
    
    def format_number(self, value):
        """Format number removing excess trailing zeros"""
        if abs(value) >= 1:
            # For values >= 1, use up to 6 decimal places, removing trailing zeros
            formatted = f"{value:.6f}".rstrip('0').rstrip('.')
        else:
            # For small values, use scientific notation
            formatted = f"{value:.6e}"
            # Remove trailing zeros from mantissa
            parts = formatted.split('e')
            mantissa = parts[0].rstrip('0').rstrip('.')
            formatted = f"{mantissa}e{parts[1]}"
        return formatted
    
    def save_parameters(self):
        """Save measurement parameters to JSON file"""
        if not self.user_manager:
            QMessageBox.warning(self, "Erro", "Sistema de usuários não disponível")
            return
        
        # Use last directory if available, otherwise use default
        if IVMeasurementBlock._last_params_dir:
            start_dir = IVMeasurementBlock._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory("configs/presets")
            start_dir = str(params_dir)
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Parâmetros", start_dir, "JSON Files (*.json)"
        )
        
        if filename:
            # Remember this directory for next time
            IVMeasurementBlock._last_params_dir = os.path.dirname(filename)
            parameters = {
                "measurement_type": "iv",
                "instrument_type": "smu_2450",
                "v_start": self.v_start_spin.value(),
                "v_stop": self.v_stop_spin.value(),
                "v_step": self.v_step_spin.value(),
                "delay": self.delay_spin.value(),
                "current_limit": self.ilim_spin.value(),
                "nplc": self.nplc_spin.value(),
                "count": int(self.count_spin.value()),
                "dual_sweep": self.dual_checkbox.isChecked(),
                "saved_at": datetime.now().isoformat()
            }
            
            try:
                with open(filename, 'w') as f:
                    json.dump(parameters, f, indent=2)
                QMessageBox.information(self, "Sucesso", "Parâmetros salvos com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar parâmetros: {e}")
    
    def load_parameters(self):
        """Load measurement parameters from JSON or exported measurement file"""
        if not self.user_manager:
            QMessageBox.warning(self, "Erro", "Sistema de usuários não disponível")
            return
        
        # Use last directory if available, otherwise use default
        if IVMeasurementBlock._last_params_dir:
            start_dir = IVMeasurementBlock._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory("configs/presets")
            start_dir = str(params_dir)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Parâmetros", start_dir, 
            "Parameter Files (*.json *.txt);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            # Remember this directory for next time
            IVMeasurementBlock._last_params_dir = os.path.dirname(filename)
            try:
                if filename.endswith('.json'):
                    # Load from JSON parameter file
                    with open(filename, 'r') as f:
                        parameters = json.load(f)
                    
                    if parameters.get("measurement_type") != "iv":
                        QMessageBox.warning(self, "Aviso", "Arquivo não é de medição I-V")
                        return
                    
                    self.v_start_spin.setValue(parameters.get("v_start", 0.0))
                    self.v_stop_spin.setValue(parameters.get("v_stop", 5.0))
                    self.v_step_spin.setValue(parameters.get("v_step", 0.1))
                    self.delay_spin.setValue(parameters.get("delay", 0.05))
                    self.ilim_spin.setValue(parameters.get("current_limit", 1e-3))
                    self.nplc_spin.setValue(parameters.get("nplc", 1.0))
                    self.count_spin.setValue(parameters.get("count", 1))
                    self.dual_checkbox.setChecked(parameters.get("dual_sweep", False))
                    
                elif filename.endswith('.txt'):
                    # Load from exported measurement file (extract parameters from header)
                    with open(filename, 'r') as f:
                        for line in f:
                            if line.startswith('#'):
                                if 'V start (V):' in line:
                                    self.v_start_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'V stop (V):' in line:
                                    self.v_stop_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Step (V):' in line:
                                    self.v_step_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Delay (s):' in line:
                                    self.delay_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Limite corrente (A):' in line or 'Limite de corrente (A):' in line:
                                    self.ilim_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'NPLC:' in line:
                                    self.nplc_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Count:' in line:
                                    self.count_spin.setValue(int(line.split(':')[1].strip()))
                                elif 'Dual sweep:' in line:
                                    self.dual_checkbox.setChecked('True' in line)
                
                QMessageBox.information(self, "Sucesso", "Parâmetros carregados com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar parâmetros: {e}")
    
    def export_measurement(self):
        """Export complete measurement with metadata"""
        if not self.readings:
            QMessageBox.warning(self, "Aviso", "Nenhuma leitura para exportar")
            return
        
        # Determine save location - use last directory if available
        default_filename = f"iv_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        
        if IVMeasurementBlock._last_export_dir:
            default_path = os.path.join(IVMeasurementBlock._last_export_dir, default_filename)
        elif self.user_manager:
            export_dir = self.user_manager.get_user_directory("exports")
            default_path = str(export_dir / default_filename)
        else:
            default_path = default_filename
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar Medição", default_path, "Text Files (*.txt)"
        )
        
        if filename:
            # Remember this directory for next time
            IVMeasurementBlock._last_export_dir = os.path.dirname(filename)
            try:
                with open(filename, "w") as f:
                    # Metadata header
                    f.write("# Keithley LabNano3D - Medição I-V\n")
                    if self.user_manager:
                        user_info = self.user_manager.get_current_user_info()
                        user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}"
                        f.write(f"# Usuário: {user_name}\n")
                    f.write("# Equipamento: SMU 2450\n")
                    f.write(f"# Data início: {self.start_time}\n")
                    if self.first_reading_time:
                        f.write(f"# Primeira leitura: {self.first_reading_time}\n")
                    f.write(f"# Data fim: {datetime.now()}\n")
                    f.write("#\n")
                    f.write("# Parâmetros de Medição:\n")
                    f.write(f"# V start (V): {self.v_start_spin.value()}\n")
                    f.write(f"# V stop (V): {self.v_stop_spin.value()}\n")
                    f.write(f"# Step (V): {self.v_step_spin.value()}\n")
                    f.write(f"# Delay (s): {self.delay_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Count: {int(self.count_spin.value())}\n")
                    f.write(f"# Dual sweep: {self.dual_checkbox.isChecked()}\n")
                    f.write(f"# Número de leituras: {len(self.readings)}\n")
                    total_time = datetime.now() - self.start_time
                    f.write(f"# Tempo total de medição: {total_time}\n")
                    f.write("# ---\n")
                    
                    # Data
                    f.write("Tempo_(s)\tCorrente_(A)\tTensao_(V)\n")
                    for t, i, v in self.readings:
                        f.write(f"{t:.2f}\t{i:.6e}\t{v:.6e}\n")
                
                QMessageBox.information(self, "Sucesso", f"Medição exportada para:\n{filename}")
                
                # Clean up temporary file if it exists
                if self.temp_file_path and os.path.exists(self.temp_file_path):
                    try:
                        os.remove(self.temp_file_path)
                    except OSError:
                        pass
                        
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar medição: {e}")
    
    def load_measurement(self):
        """Load previous measurement to view in graph"""
        # Use last directory if available, otherwise use default
        if IVMeasurementBlock._last_load_dir:
            start_dir = IVMeasurementBlock._last_load_dir
        elif self.user_manager:
            measurements_dir = self.user_manager.get_user_directory("exports")
            start_dir = str(measurements_dir)
        else:
            start_dir = ""
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Medição", start_dir, "Text Files (*.txt)"
        )
        
        if filename:
            # Remember this directory for next time
            IVMeasurementBlock._last_load_dir = os.path.dirname(filename)
            try:
                readings = []
                with open(filename, 'r') as f:
                    for line in f:
                        # Skip comments and headers
                        if line.startswith('#') or line.startswith('Tempo'):
                            continue
                        
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            try:
                                t = float(parts[0])
                                i = float(parts[1])
                                v = float(parts[2])
                                readings.append((t, i, v))
                            except ValueError:
                                continue
                
                if readings:
                    # Update display with loaded data (without starting measurement)
                    self.list_widget.clear()
                    for t, i, v in readings:
                        self.list_widget.addItem(
                            f"{t:.2f} s | I = {self.format_number(i)} A | V = {self.format_number(v)} V"
                        )
                    
                    # Update graph
                    x = [r[2] for r in readings]
                    y = [r[1] for r in readings]
                    self.curve.setData(x, y)
                    
                    # Update stats
                    elapsed_str = str(timedelta(seconds=int(readings[-1][0])))
                    self.stats_label.setText(f"Total de leituras: {len(readings)} | Tempo: {elapsed_str} (Carregada)")
                    
                    QMessageBox.information(self, "Sucesso", f"Medição carregada: {len(readings)} pontos")
                else:
                    QMessageBox.warning(self, "Aviso", "Nenhum dado válido encontrado no arquivo")
                    
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar medição: {e}")

