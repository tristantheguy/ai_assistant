from PyQt5 import QtWidgets, QtCore


class FloatingWindow(QtWidgets.QWidget):
    """Small window that stays on top and shows messages."""

    message_signal = QtCore.pyqtSignal(str)

    def __init__(self, on_submit=None):
        super().__init__()
        self.on_submit = on_submit
        self.setWindowTitle("AI Assistant")
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint
        )
        self.resize(300, 200)

        self._drag_pos = None

        layout = QtWidgets.QVBoxLayout(self)
        self.log_box = QtWidgets.QTextEdit(self)
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)
        self.input = QtWidgets.QLineEdit(self)
        self.input.returnPressed.connect(self._send_input)
        layout.addWidget(self.input)

        self.message_signal.connect(self._append_message)

        # Show an initial friendly message
        self.display_message("👋 I'm your assistant! (Drag me around)")

    def _append_message(self, text: str):
        self.log_box.append(text)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )

    def display_message(self, text):
        self.message_signal.emit(text)

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
