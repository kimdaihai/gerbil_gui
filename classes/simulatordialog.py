from lib.qt.gerbil_gui.ui_simulatordialog import Ui_SimulatorDialog

from .simulatorwidget import SimulatorWidget

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt, QCoreApplication, QTimer
from PyQt5.QtGui import QColor,QPalette
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QSlider, QLabel, QPushButton, QWidget, QDialog, QMainWindow, QFileDialog, QLineEdit, QSpacerItem, QListWidgetItem, QMenuBar, QMenu, QAction, QTableWidgetItem, QDialog

class SimulatorDialog(QWidget, Ui_SimulatorDialog):
    def __init__(self, parent, refresh_rate=20):
        super(SimulatorDialog, self).__init__()
        self.setupUi(self)
        
        self.simulator_widget = SimulatorWidget(self, refresh_rate)
        self.gridLayout_simulator.addWidget(self.simulator_widget)