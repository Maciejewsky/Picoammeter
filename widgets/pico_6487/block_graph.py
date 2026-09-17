from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class GraphBlock(QGroupBox):
    def __init__(self):
        super().__init__("Gráfico das Leituras")
        layout = QVBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_data(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y, marker='o')
        ax.set_xlabel("Tempo")
        ax.set_ylabel("Valor")
        ax.grid(True)
        self.canvas.draw()
