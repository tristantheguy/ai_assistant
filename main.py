import sys
from PyQt5 import QtWidgets
from floating_ui import FloatingWindow
from agent import ClippyAgent
from error_handler import ErrorReporter

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = FloatingWindow()
    window.show()

    agent = ClippyAgent(window)
    window.on_submit = agent.handle_text
    agent.start()

    exit_code = app.exec_()
    agent.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    reporter = ErrorReporter()
    try:
        main()
    except Exception:
        reporter.handle_exception()

