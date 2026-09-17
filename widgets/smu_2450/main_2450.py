# widgets/smu_2450/main_2450.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from widgets.smu_2450.block_source_control import SourceControlBlock
from widgets.smu_2450.block_resistance_time import ResistanceMeasurementBlock
from widgets.smu_2450.block_iv_measurement import IVMeasurementBlock


class SMU2450Widget(QWidget):
    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument

        main_layout = QVBoxLayout(self)

        # Abas para escolher função
        tabs = QTabWidget()
        tabs.addTab(ResistanceMeasurementBlock(self.instrument), "Resistência")
        tabs.addTab(IVMeasurementBlock(self.instrument), "I x V")
        tabs.addTab(SourceControlBlock(self.instrument), "Fonte")

        main_layout.addWidget(tabs)
