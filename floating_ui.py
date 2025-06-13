from PyQt5 import QtWidgets, QtCore

class FloatingWindow(QtWidgets.QWidget):
    """Small window that stays on top and shows messages."""

    def __init__(self, on_submit=None):
        super().__init__()
        self.on_submit = on_submit
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
        )
        self.resize(250, 120)

        self._drag_pos = None

        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("", self)
        self.label.setWordWrap(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)
        self.input = QtWidgets.QLineEdit(self)
        self.input.returnPressed.connect(self._send_input)
        layout.addWidget(self.input)

        # Show an initial friendly message
        self.display_message("👋 I'm your assistant! (Drag me around)")

    def display_message(self, text):
        self.label.setText(text)

    def _send_input(self):
        text = self.input.text().strip()
        if text and self.on_submit:
            self.on_submit(text)
        self.input.clear()

    # -- Drag Support -----------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()
