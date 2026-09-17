import tkinter as tk
from tkinter import ttk


class ReadingsFrame(ttk.LabelFrame):
    def __init__(self, parent, instrument):
        super().__init__(parent, text="Leituras", padding="10")
        self.instrument = instrument

        self.setup_widgets()

    def setup_widgets(self):
        """Configura os widgets do frame"""
        # Área de texto para leituras
        self.readings_text = tk.Text(self, height=20, width=40, state='disabled')
        self.readings_text.pack(fill=tk.BOTH, expand=True)

        # Barra de rolagem
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.readings_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.readings_text.config(yscrollcommand=scrollbar.set)

    def update_readings(self, text):
        """Atualiza a área de leituras"""
        self.readings_text.config(state='normal')
        self.readings_text.insert(tk.END, text)
        self.readings_text.see(tk.END)
        self.readings_text.config(state='disabled')