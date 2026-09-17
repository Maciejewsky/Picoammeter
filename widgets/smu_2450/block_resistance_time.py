# widgets/smu_2450/block_resistance_time.py

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QListWidget, QSplitter, QFileDialog, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import json
import os

class ResistanceMeasurementBlock(QWidget):
    # Class variables to remember last used directories
    _last_params_dir = None
    _last_export_dir = None
    _last_load_dir = None
    
    def __init__(self, instrument, user_manager=None, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.user_manager = user_manager
        self.measuring = False
        self.readings = []  # Lista de tuplas (tempo_relativo_s, resistencia)
        self.start_time = None
        self.first_reading_time = None
        self.last_buffer_index = 0  # índice do último ponto lido
        self.temp_file_path = None  # Path to temporary save file

        self.measure_timer = QTimer()
        self.measure_timer.timeout.connect(self.acquire_reading)

        splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter)

        # ----- Controles (esquerda) -----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Parameters group
        params_group = QGroupBox("Parâmetros de Medição")
        params_layout = QVBoxLayout()
        
        # Tensão aplicada
        hlayout_v = QHBoxLayout()
        hlayout_v.addWidget(QLabel("Tensão (V):"))
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(-210, 210)
        self.voltage_spin.setDecimals(3)
        self.voltage_spin.setValue(1.0)
        hlayout_v.addWidget(self.voltage_spin)
        params_layout.addLayout(hlayout_v)

        # Limite de corrente - with improved formatting
        hlayout_ilim = QHBoxLayout()
        hlayout_ilim.addWidget(QLabel("Limite de corrente (A):"))
        self.ilim_spin = QDoubleSpinBox()
        self.ilim_spin.setRange(1e-9, 1.0)
        self.ilim_spin.setDecimals(9)
        self.ilim_spin.setValue(1e-3)
        # Remove trailing zeros in display
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

        # Intervalo entre leituras
        hlayout_t = QHBoxLayout()
        hlayout_t.addWidget(QLabel("Intervalo (s):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 60)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setValue(1.0)
        hlayout_t.addWidget(self.interval_spin)
        params_layout.addLayout(hlayout_t)
        
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

        # ----- Gráfico (direita) -----
        self.plot_widget = pg.PlotWidget(title="Resistência vs Tempo")
        self.plot_widget.setLabel('left', 'Resistência (Ω)')
        self.plot_widget.setLabel('bottom', 'Tempo (s)')
        self.curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='r', width=2))
        splitter.addWidget(self.plot_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    # ----- Controle de medição -----
    def toggle_measurement(self, checked):
        if checked:
            self.start_measurement()
        else:
            self.stop_measurement()

    def start_measurement(self):
        self.measuring = True
        self.readings.clear()
        self.list_widget.clear()
        self.start_time = datetime.now()
        self.first_reading_time = None
        self.last_buffer_index = 0
        self.toggle_button.setText("Parar Medição")
        self.curve.setData([], [])
        
        # Create temporary file for auto-save
        if self.user_manager:
            temp_dir = self.user_manager.get_user_directory("measurements/resistance")
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            self.temp_file_path = temp_dir / f"temp_resistance_{timestamp}.txt"
        else:
            self.temp_file_path = None

        # Configura SMU
        try:
            self.instrument.write("reset()")
            self.instrument.write("smu.source.func = smu.FUNC_DC_VOLTAGE")
            self.instrument.write(f"smu.source.ilimit.level = {self.ilim_spin.value()}")
            self.instrument.write(f"smu.source.level = {self.voltage_spin.value()}")
            #self.instrument.write("smu.measure.func = smu.FUNC_RESISTANCE")
            self.instrument.write("smu.measure.unit = smu.UNIT_OHM")
            self.instrument.write("smu.measure.terminals = smu.TERMINALS_FRONT")
            self.instrument.write("smu.measure.autorange = smu.ON")
            self.instrument.write(f"smu.measure.nplc = {self.nplc_spin.value()}")
            self.instrument.write("smu.source.output = smu.ON")
        except Exception as e:
            print(f"Erro ao configurar SMU: {e}")
            self.stop_measurement()
            return

        # Inicia timer de leitura
        interval_ms = int(self.interval_spin.value() * 1000)
        self.measure_timer.start(interval_ms)

    def stop_measurement(self):
        self.measuring = False
        self.measure_timer.stop()
        self.toggle_button.setText("Iniciar Medição")
        if self.instrument:
            try:
                self.instrument.write("smu.source.output = smu.OFF")
            except Exception as e:
                print(f"Erro ao desligar SMU: {e}")

    def acquire_reading(self):
        if not self.measuring or self.instrument is None:
            return
        try:
            # Mede corrente e calcula resistência
            resistance = float(self.instrument.query("print(smu.measure.read())"))

            if self.first_reading_time is None:
                self.first_reading_time = datetime.now()
            
            relative_time = (datetime.now() - self.start_time).total_seconds()
            self.readings.append((relative_time, resistance))

            # Auto-save to temporary file
            self.auto_save_reading(relative_time, resistance)
            
            self.update_display()
        except Exception as e:
            print(f"Erro na leitura: {e}")
            self.stop_measurement()
    
    def auto_save_reading(self, time, resistance):
        """Auto-save reading to temporary file"""
        if not self.temp_file_path:
            return
        
        try:
            # Create file with header if it doesn't exist
            if not os.path.exists(self.temp_file_path):
                with open(self.temp_file_path, 'w') as f:
                    f.write(f"# Auto-save temporário - Medição de Resistência\n")
                    f.write(f"# Início: {self.start_time}\n")
                    f.write(f"# Tensão (V): {self.voltage_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
                    f.write("Tempo_(s)\tResistencia_(Ohms)\n")
            
            # Append reading
            with open(self.temp_file_path, 'a') as f:
                f.write(f"{time:.2f}\t{resistance:.6e}\n")
        except Exception as e:
            print(f"Erro ao salvar temporariamente: {e}")

    def update_display(self):
        if self.readings:
            t, val = self.readings[-1]
            # Use formatted number for display
            self.list_widget.addItem(f"{t:.2f} s | {self.format_number(val)} Ω")
            self.list_widget.scrollToBottom()

            elapsed_str = str(timedelta(seconds=int(t)))
            self.stats_label.setText(f"Total de leituras: {len(self.readings)} | Tempo: {elapsed_str}")

            x = [r[0] for r in self.readings]
            y = [r[1] for r in self.readings]
            self.curve.setData(x, y)
    
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
        if ResistanceMeasurementBlock._last_params_dir:
            start_dir = ResistanceMeasurementBlock._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory("configs/presets")
            start_dir = str(params_dir)
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Parâmetros", start_dir, "JSON Files (*.json)"
        )
        
        if filename:
            # Remember this directory for next time
            ResistanceMeasurementBlock._last_params_dir = os.path.dirname(filename)
            parameters = {
                "measurement_type": "resistance",
                "instrument_type": "smu_2450",
                "voltage": self.voltage_spin.value(),
                "current_limit": self.ilim_spin.value(),
                "nplc": self.nplc_spin.value(),
                "interval": self.interval_spin.value(),
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
        if ResistanceMeasurementBlock._last_params_dir:
            start_dir = ResistanceMeasurementBlock._last_params_dir
        else:
            params_dir = self.user_manager.get_user_directory("configs/presets")
            start_dir = str(params_dir)
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Parâmetros", start_dir, 
            "Parameter Files (*.json *.txt);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            # Remember this directory for next time
            ResistanceMeasurementBlock._last_params_dir = os.path.dirname(filename)
            try:
                if filename.endswith('.json'):
                    # Load from JSON parameter file
                    with open(filename, 'r') as f:
                        parameters = json.load(f)
                    
                    if parameters.get("measurement_type") != "resistance":
                        QMessageBox.warning(self, "Aviso", "Arquivo não é de medição de resistência")
                        return
                    
                    self.voltage_spin.setValue(parameters.get("voltage", 1.0))
                    self.ilim_spin.setValue(parameters.get("current_limit", 1e-3))
                    self.nplc_spin.setValue(parameters.get("nplc", 1.0))
                    self.interval_spin.setValue(parameters.get("interval", 1.0))
                    
                elif filename.endswith('.txt'):
                    # Load from exported measurement file (extract parameters from header)
                    with open(filename, 'r') as f:
                        for line in f:
                            if line.startswith('#'):
                                if 'Tensão (V):' in line:
                                    self.voltage_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Limite corrente (A):' in line or 'Limite de corrente (A):' in line:
                                    self.ilim_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'NPLC:' in line:
                                    self.nplc_spin.setValue(float(line.split(':')[1].strip()))
                                elif 'Intervalo (s):' in line:
                                    self.interval_spin.setValue(float(line.split(':')[1].strip()))
                
                QMessageBox.information(self, "Sucesso", "Parâmetros carregados com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar parâmetros: {e}")
    
    def export_measurement(self):
        """Export complete measurement with metadata"""
        if not self.readings:
            QMessageBox.warning(self, "Aviso", "Nenhuma leitura para exportar")
            return
        
        # Determine save location - use last directory if available
        default_filename = f"resistance_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        
        if ResistanceMeasurementBlock._last_export_dir:
            default_path = os.path.join(ResistanceMeasurementBlock._last_export_dir, default_filename)
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
            ResistanceMeasurementBlock._last_export_dir = os.path.dirname(filename)
            try:
                with open(filename, "w") as f:
                    # Metadata header
                    f.write("# Keithley LabNano3D - Medição de Resistência\n")
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
                    f.write(f"# Tensão (V): {self.voltage_spin.value()}\n")
                    f.write(f"# Limite corrente (A): {self.format_number(self.ilim_spin.value())}\n")
                    f.write(f"# NPLC: {self.nplc_spin.value()}\n")
                    f.write(f"# Intervalo (s): {self.interval_spin.value()}\n")
                    f.write(f"# Número de leituras: {len(self.readings)}\n")
                    total_time = datetime.now() - self.start_time
                    f.write(f"# Tempo total de medição: {total_time}\n")
                    f.write("# ---\n")
                    
                    # Data
                    f.write("Tempo_(s)\tResistencia_(Ohms)\n")
                    for t, val in self.readings:
                        f.write(f"{t:.2f}\t{val:.6e}\n")
                
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
        if ResistanceMeasurementBlock._last_load_dir:
            start_dir = ResistanceMeasurementBlock._last_load_dir
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
            ResistanceMeasurementBlock._last_load_dir = os.path.dirname(filename)
            try:
                readings = []
                with open(filename, 'r') as f:
                    for line in f:
                        # Skip comments and headers
                        if line.startswith('#') or line.startswith('Tempo'):
                            continue
                        
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            try:
                                t = float(parts[0])
                                val = float(parts[1])
                                readings.append((t, val))
                            except ValueError:
                                continue
                
                if readings:
                    # Update display with loaded data (without starting measurement)
                    self.list_widget.clear()
                    for t, val in readings:
                        self.list_widget.addItem(f"{t:.2f} s | {self.format_number(val)} Ω")
                    
                    # Update graph
                    x = [r[0] for r in readings]
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

