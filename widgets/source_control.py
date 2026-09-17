import tkinter as tk
from tkinter import ttk, messagebox


class SourceControlFrame(ttk.LabelFrame):
    def __init__(self, parent, instrument):
        super().__init__(parent, text="Controle da Fonte (TSP)", padding="10")
        self.instrument = instrument
        self.output_state = False

        self.setup_widgets()
        self.initialize_instrument()

    def setup_widgets(self):
        """Configura os widgets do frame"""
        # Modo de operação
        ttk.Label(self, text="Modo:").grid(row=0, column=0, sticky=tk.W)
        self.source_mode = tk.StringVar(value='VOLT')
        ttk.Radiobutton(self, text="Tensão", variable=self.source_mode, value='VOLT',
                        command=self.update_source_mode).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(self, text="Corrente", variable=self.source_mode, value='CURR',
                        command=self.update_source_mode).grid(row=2, column=0, sticky=tk.W)

        # Valor da fonte
        ttk.Label(self, text="Valor:").grid(row=0, column=1, sticky=tk.W)
        self.source_value = ttk.Entry(self, width=10)
        self.source_value.insert(0, "0")
        self.source_value.bind("<Return>", self.update_source_value)
        self.source_value.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(self, text="V ou A").grid(row=2, column=1, sticky=tk.W)

        # Limite de proteção
        ttk.Label(self, text="Limite:").grid(row=0, column=2, sticky=tk.W)
        self.compliance_value = ttk.Entry(self, width=10)
        self.compliance_value.insert(0, "1e-3")  # Valor padrão 1mA
        self.compliance_value.bind("<Return>", self.update_compliance)
        self.compliance_value.grid(row=1, column=2, sticky=tk.W, padx=5)
        ttk.Label(self, text="A ou V").grid(row=2, column=2, sticky=tk.W)

        # Botão de saída
        self.output_button = ttk.Button(self, text="Ligar Saída", command=self.toggle_output)
        self.output_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Configurar pesos
        for i in range(3):
            self.columnconfigure(i, weight=1)

    def initialize_instrument(self):
        """Configuração inicial do instrumento conforme seu script"""
        try:
            # Envia o script de inicialização completo
            init_script = """
            -- Reseta o instrumento para os padrões de fábrica
            reset()

            -- Configuração padrão da fonte
            smua.source.func = smua.FUNC_DC_VOLTAGE
            smua.source.ilimit.level = 1e-3
            smua.source.level = 0

            -- Configuração padrão de medição
            smua.measure.func = smua.FUNC_DC_CURRENT
            smua.measure.unit = smua.UNIT_AMP
            smua.measure.terminals = smua.TERMINALS_FRONT
            smua.measure.autorange = smua.ON
            smua.measure.nplc = 1

            -- Desliga a saída inicialmente
            smua.source.output = smua.OFF
            """
            self.instrument.write(init_script)

            # Configura o modo inicial
            self.update_source_mode()
            self.update_compliance()

        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Falha ao configurar instrumento: {str(e)}")

    def update_source_mode(self, event=None):
        """Atualiza o modo de operação (Tensão/Corrente) usando TSP"""
        try:
            mode = self.source_mode.get()
            if mode == 'VOLT':
                script = """
                smua.source.func = smua.FUNC_DC_VOLTAGE
                smua.measure.func = smua.FUNC_DC_CURRENT
                """
            else:
                script = """
                smua.source.func = smua.FUNC_DC_AMPS
                smua.measure.func = smua.FUNC_DC_VOLTAGE
                """

            self.instrument.write(script)
            self.update_source_value()  # Atualiza o valor com o novo modo

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar modo: {str(e)}")

    def update_source_value(self, event=None):
        """Atualiza o valor da fonte usando TSP"""
        try:
            value = float(self.source_value.get())
            script = f"""
            smua.source.level = {value}
            """
            self.instrument.write(script)

        except ValueError:
            messagebox.showerror("Erro", "Insira um valor numérico válido")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar valor: {str(e)}")

    def update_compliance(self, event=None):
        """Atualiza o limite de proteção usando TSP"""
        try:
            compliance = float(self.compliance_value.get())
            mode = self.source_mode.get()

            if mode == 'VOLT':
                script = f"smua.source.ilimit.level = {compliance}"
            else:
                script = f"smua.source.vlimit.level = {compliance}"

            self.instrument.write(script)

        except ValueError:
            messagebox.showerror("Erro", "Insira um valor numérico válido")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar limite: {str(e)}")

    def toggle_output(self):
        """Ativa/desativa a saída da fonte usando TSP"""
        try:
            if not self.output_state:
                # Ligar saída
                script = """
                smua.source.output = smua.ON
                """
                self.instrument.write(script)
                self.output_state = True
                self.output_button.config(text="Desligar Saída")
                messagebox.showinfo("Saída", "Saída habilitada com sucesso")
            else:
                # Desligar saída
                script = """
                smua.source.output = smua.OFF
                """
                self.instrument.write(script)
                self.output_state = False
                self.output_button.config(text="Ligar Saída")
                messagebox.showinfo("Saída", "Saída desabilitada com sucesso")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao controlar saída: {str(e)}")