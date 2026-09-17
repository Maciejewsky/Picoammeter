# widgets/pico_6487/block_iv_measurement.py (versão ajustada)

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QMessageBox, QGroupBox, QCheckBox
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
        self.first_reading_time = None
        self.start_time = None
        self.temp_file_path = None  # Path to temporary save file
        self.sweep_direction = 1  # 1 for forward, -1 for reverse
        self.dual_sweep_active = False  # Track if we're in the return sweep

        self.measure_timer = QTimer()
        self.measure_timer.timeout.connect(self.acquire_reading)

        splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)

        # Controles e leituras (esquerda)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Parameters group
        params_group = QGroupBox("Parâmetros de Medição")
        params_layout = QVBoxLayout()

        # V start
        hlayout_start = QHBoxLayout()
        hlayout_start.addWidget(QLabel("V start (V):"))
        self.v_start_spin = QDoubleSpinBox()
        self.v_start_spin.setRange(-505, 505)
        self.v_start_spin.setDecimals(3)
        self.v_start_spin.setValue(-10.0)
        hlayout_start.addWidget(self.v_start_spin)
        params_layout.addLayout(hlayout_start)

        # V stop
        hlayout_stop = QHBoxLayout()
        hlayout_stop.addWidget(QLabel("V stop (V):"))
        self.v_stop_spin = QDoubleSpinBox()
        self.v_stop_spin.setRange(-505, 505)
        self.v_stop_spin.setDecimals(3)
        self.v_stop_spin.setValue(10.0)
        hlayout_stop.addWidget(self.v_stop_spin)
        params_layout.addLayout(hlayout_stop)

        # Step
        hlayout_step = QHBoxLayout()
        hlayout_step.addWidget(QLabel("Step (V):"))
        self.v_step_spin = QDoubleSpinBox()
        self.v_step_spin.setRange(0.001, 100)
        self.v_step_spin.setDecimals(3)
        self.v_step_spin.setValue(0.1)
        hlayout_step.addWidget(self.v_step_spin)
        params_layout.addLayout(hlayout_step)

        # Limite de corrente - with improved formatting
        hlayout_ilim = QHBoxLayout()
        hlayout_ilim.addWidget(QLabel("Limite de corrente (A):"))
        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(2.5e-6, 2.5e-2)
        self.ilim_spin.setDecimals(6)
        self.ilim_spin.setValue(0.025)
        self.ilim_spin.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        hlayout_ilim.addWidget(self.ilim_spin)
        params_layout.addLayout(hlayout_ilim)

        # NPLC
        hlayout_nplc = QHBoxLayout()
        hlayout_nplc.addWidget(QLabel("NPLC:"))
        self.nplc_spin = QDoubleSpinBox()
        self.nplc_spin.setRange(0.1, 6.0)
        self.nplc_spin.setDecimals(1)
        self.nplc_spin.setValue(1.0)
        hlayout_nplc.addWidget(self.nplc_spin)
        params_layout.addLayout(hlayout_nplc)

        # Intervalo
        hlayout_t = QHBoxLayout()
        hlayout_t.addWidget(QLabel("Intervalo (s):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 60)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setValue(0.5)
        hlayout_t.addWidget(self.interval_spin)
        params_layout.addLayout(hlayout_t)
        
        # Dual sweep checkbox
        self.dual_sweep_checkbox = QCheckBox("Varredura Dual (ida e volta)")
        self.dual_sweep_checkbox.setToolTip("Quando marcado, a medição vai de V start a V stop e volta de V stop a V start")
        params_layout.addWidget(self.dual_sweep_checkbox)
        
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
        self.toggle_button = QPushButton("Iniciar Medição")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_measurement)
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

        # Gráfico I-V (direita)
        self.plot_widget = pg.PlotWidget(title="I-V")
        self.plot_widget.setLabel('left', 'Corrente (A)')
        self.plot_widget.setLabel('bottom', 'Tensão (V)')
        self.curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='r', width=2))
        splitter.addWidget(self.plot_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    def toggle_measurement(self, checked):
        if checked:
            self.start_measurement()
        else:
            self.stop_measurement()

    def start_measurement(self):
        self.measuring = True
        self.readings.clear()
        self.list_widget.clear()
        self.alert_label.setText("")
        self.first_reading_time = None
        self.start_time = datetime.now()
        self.toggle_button.setText("Parar Medição")
        self.curve.setData([], [])
        self.sweep_direction = 1  # Start with forward sweep
        self.dual_sweep_active = False  # Not in return sweep yet
        
        # Create temporary file for auto-save
        if self.user_manager:
            temp_dir = self.user_manager.get_user_directory("measurements/iv")
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            self.temp_file_path = temp_dir / f"temp_iv_pico_{timestamp}.txt"
        else:
            self.temp_file_path = None

        # Configuração sequencial do instrumento
        self.configure_instrument_step(0)

    def stop_measurement(self):
        self.measuring = False
        self.measure_timer.stop()
        self.toggle_button.setText("Iniciar Medição")
        if self.instrument:
            try:
                self.instrument.write("SOUR:VOLT:STAT OFF")
            except Exception as e:
                print(f"Erro ao desligar fonte: {e}")

    def configure_instrument_step(self, step):
        v_start = self.v_start_spin.value()
        v_stop = self.v_stop_spin.value()
        v_step = self.v_step_spin.value()
        i_limit = self.ilim_spin.value()
        nplc = self.nplc_spin.value()

        try:
            commands = [
                "*RST",
                "FORM:ELEM READ,VSO",
                "SYST:ZCH ON",
                f"SENS:CURR:NPLC {nplc}",
                f"SOUR:VOLT:ILIM {i_limit}",
                "SOUR:VOLT:STAT ON",
                "SYST:ZCH OFF"
            ]

            if step < len(commands):
                self.instrument.write(commands[step])
                QTimer.singleShot(200, lambda: self.configure_instrument_step(step + 1))
            else:
                self.v_current = v_start
                self.v_stop_value = v_stop
                self.v_step_value = v_step
                self.instrument.write(f"SOUR:VOLT {self.v_current}")  # aplica tensão inicial
                self.measure_timer.start(int(self.interval_spin.value() * 1000))

        except Exception as e:
            print(f"Erro na configuração do instrumento: {e}")
            self.stop_measurement()

    def acquire_reading(self):
        if not self.measuring or self.instrument is None:
            return

        try:
            response = self.instrument.query("READ?")
            current, voltage = [float(v) for v in response.strip().split(",")]

            # Verifica limite de corrente
            i_limit = self.ilim_spin.value()
            if abs(current) > i_limit:
                self.alert_label.setText("Limite de corrente excedido!")
                self.stop_measurement()
                return

            self.alert_label.setText("")

            if self.first_reading_time is None:
                self.first_reading_time = datetime.now()
                relative_time = 0.0
            else:
                relative_time = (datetime.now() - self.first_reading_time).total_seconds()

            self.readings.append((relative_time, current, voltage))
            self.update_display()

            # Incrementa tensão com direção da varredura
            step = self.v_step_value * self.sweep_direction
            self.v_current += step
            
            # Check if we've reached the end of current sweep
            reached_end = False
            if self.sweep_direction > 0:  # Forward sweep
                if step > 0:
                    reached_end = self.v_current > self.v_stop_value
                else:
                    reached_end = self.v_current < self.v_stop_value
            else:  # Reverse sweep
                v_start = self.v_start_spin.value()
                if step > 0:
                    reached_end = self.v_current > v_start
                else:
                    reached_end = self.v_current < v_start
            
            if reached_end:
                # Check if we need to do return sweep
                if self.dual_sweep_checkbox.isChecked() and not self.dual_sweep_active:
                    # Start return sweep
                    self.dual_sweep_active = True
                    self.sweep_direction = -1
                    self.v_current = self.v_stop_value
                    self.instrument.write(f"SOUR:VOLT {self.v_current}")
                else:
                    # Measurement complete
                    self.stop_measurement()
            else:
                self.instrument.write(f"SOUR:VOLT {self.v_current}")

        except Exception as e:
            print(f"Erro ao adquirir leitura: {e}")
            self.stop_measurement()

    def update_display(self):
        if self.readings:
            t, current, voltage = self.readings[-1]
            # Use formatted numbers for display
            self.list_widget.addItem(
                f"{t:.2f} s | I = {self.format_number(current)} A | V = {self.format_number(voltage)} V"
            )
            self.list_widget.scrollToBottom()

            elapsed_str = str(timedelta(seconds=int(t)))
            self.stats_label.setText(f"Total de leituras: {len(self.readings)} | Tempo: {elapsed_str}")

            x = [r[2] for r in self.readings]  # tensão
            y = [r[1] for r in self.readings]  # corrente
            self.curve.setData(x, y)
            
            # Auto-save reading
            self.auto_save_reading(t, current, voltage)
    
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
                    f.write(f"# Auto-save temporário - Medição I-V (Pico 6487)\n")
                    f.write(f"# Início: {self.start_time}\n")
                    f.write(f"# Modo: {'Varredura Dual' if self.dual_sweep_checkbox.isChecked() else 'Varredura Simples'}\n")
                    f.write(f"# V start (V): {self.v_start_spin.value()}\n")
                    f.write(f"# V stop (V): {self.v_stop_spin.value()}\n")
                    f.write(f"# Step (V): {self.v_step_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
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
                "instrument_type": "pico_6487",
                "v_start": self.v_start_spin.value(),
                "v_stop": self.v_stop_spin.value(),
                "v_step": self.v_step_spin.value(),
                "current_limit": self.ilim_spin.value(),
                "nplc": self.nplc_spin.value(),
                "interval": self.interval_spin.value(),
                "dual_sweep": self.dual_sweep_checkbox.isChecked(),
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
                    
                    self.v_start_spin.setValue(parameters.get("v_start", -10.0))
                    self.v_stop_spin.setValue(parameters.get("v_stop", 10.0))
                    self.v_step_spin.setValue(parameters.get("v_step", 0.1))
                    self.ilim_spin.setValue(parameters.get("current_limit", 0.025))
                    self.nplc_spin.setValue(parameters.get("nplc", 1.0))
                    self.interval_spin.setValue(parameters.get("interval", 0.5))
                    self.dual_sweep_checkbox.setChecked(parameters.get("dual_sweep", False))
                    
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
                                elif 'Limite corrente (A):' in line or 'Limite de corrente (A):' in line:
                                    self.ilim_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'NPLC:' in line:
                                    self.nplc_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Intervalo (s):' in line:
                                    self.interval_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Modo:' in line:
                                    is_dual = 'Varredura Dual' in line
                                    self.dual_sweep_checkbox.setChecked(is_dual)
                
                QMessageBox.information(self, "Sucesso", "Parâmetros carregados com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar parâmetros: {e}")
    
    def export_measurement(self):
        """Export complete measurement with metadata"""
        if not self.readings:
            QMessageBox.warning(self, "Aviso", "Nenhuma leitura para exportar")
            return
        
        # Determine save location - use last directory if available
        default_filename = f"iv_pico_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        
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
                    f.write("# Equipamento: Picoammeter 6487\n")
                    f.write(f"# Data início: {self.start_time}\n")
                    if self.first_reading_time:
                        f.write(f"# Primeira leitura: {self.first_reading_time}\n")
                    f.write(f"# Data fim: {datetime.now()}\n")
                    f.write("#\n")
                    f.write("# Parâmetros de Medição:\n")
                    f.write(f"# Modo: {'Varredura Dual' if self.dual_sweep_checkbox.isChecked() else 'Varredura Simples'}\n")
                    f.write(f"# V start (V): {self.v_start_spin.value()}\n")
                    f.write(f"# V stop (V): {self.v_stop_spin.value()}\n")
                    f.write(f"# Step (V): {self.v_step_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
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

