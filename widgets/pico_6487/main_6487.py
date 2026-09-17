# widgets/pico_6487/main_6487.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from widgets.pico_6487.block_source_control import SourceControlBlock
from widgets.pico_6487.block_resistance_time import ResistanceMeasurementBlock
from widgets.pico_6487.block_iv_measurement import IVMeasurementBlock
from widgets.pico_6487.block_charge_discharge import ChargeDischargeBlock
from widgets.pico_6487.block_cyclic_voltammetry import CyclicVoltammetryBlock # Novo import da Voltametria

class Pico6487Widget(QWidget):
    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument

        main_layout = QVBoxLayout(self)

        # Abas para escolher função
        tabs = QTabWidget()
        tabs.addTab(
            ResistanceMeasurementBlock(self.instrument),
            "Resistência"
        )
        tabs.addTab(
            IVMeasurementBlock(self.instrument),
            "I x V"
        )
        tabs.addTab(
            ChargeDischargeBlock(self.instrument),
            "Carga / Descarga"
        )
        tabs.addTab(
            CyclicVoltammetryBlock(self.instrument),
            "Voltametria Cíclica"
        )
        tabs.addTab(
            SourceControlBlock(self.instrument),
            "Fonte"
        )

        main_layout.addWidget(tabs)