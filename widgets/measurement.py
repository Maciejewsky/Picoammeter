import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class MeasurementFrame(ttk.LabelFrame):
    def __init__(self, parent, instrument):
        super().__init__(parent, text="Configuração de Medição", padding="10")
        self.instrument = instrument
        self.measuring = False

        self.setup_widgets()

    def setup_widgets(self):
        """Configura os widgets do frame"""
        # Número de medições
        ttk.Label(self, text="Nº de Medições:").grid(row=0, column=0, sticky=tk.W)
        self.measure_count = ttk.Entry(self, width=10)
        self.measure_count.insert(0, "10")
        self.measure_count.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Intervalo entre medições
        ttk.Label(self, text="Intervalo (s):").grid(row=1, column=0, sticky=tk.W)
        self.measure_interval = ttk.Entry(self, width=10)
        self.measure_interval.insert(0, "0.5")
        self.measure_interval.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Botões de controle
        ttk.Button(self, text="Iniciar Medição", command=self.start_measurement).grid(row=2, column=0, pady=5)
        ttk.Button(self, text="Parar Medição", command=self.stop_measurement).grid(row=2, column=1, pady=5)

        # Configurar pesos
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def start_measurement(self):
        """Inicia a medição contínua"""
        if self.measuring:
            return

        try:
            count = int(self.measure_count.get())
            interval = float(self.measure_interval.get())

            # Configurar medição
            mode = self.master.source_frame.source_mode.get()
            measure_func = "CURR" if mode == 'VOLT' else "VOLT"
            self.instrument.write(f":SENS:FUNC '{measure_func}'")
            self.instrument.write(":FORM:ELEM READ")

            self.measuring = True
            self.measurement_thread = threading.Thread(
                target=self.measurement_loop,
                args=(count, interval, measure_func),
                daemon=True
            )
            self.measurement_thread.start()

        except ValueError:
            messagebox.showerror("Erro", "Insira valores válidos para contagem e intervalo")

    def stop_measurement(self):
        """Para a medição contínua"""
        self.measuring = False

    def measurement_loop(self, count, interval, measure_func):
        """Loop de medição contínua"""
        try:
            for i in range(count):
                if not self.measuring:
                    break

                try:
                    reading = self.instrument.query(f":MEAS:{measure_func}?").strip()
                    self.master.readings_frame.update_readings(f"Medição {i + 1}: {reading}\n")
                except Exception as e:
                    self.master.readings_frame.update_readings(f"Erro na medição {i + 1}: {str(e)}\n")

                time.sleep(interval)

            self.measuring = False

        except Exception as e:
            messagebox.showerror("Erro de Medição", f"Falha durante medição: {str(e)}")
            self.measuring = False