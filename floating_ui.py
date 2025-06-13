from PyQt5 import QtWidgets, QtCore

class FloatingWindow(QtWidgets.QWidget):
    """Small window that stays on top and shows messages."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
        )
        self.resize(250, 120)

        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("", self)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

    def display_message(self, text):
        self.label.setText(text)
