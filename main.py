import sys
from PyQt5 import QtWidgets
from floating_ui import FloatingWindow
from agent import ClippyAgent

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = FloatingWindow()
    window.show()

    agent = ClippyAgent(window)
    agent.start()

    exit_code = app.exec_()
    agent.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
