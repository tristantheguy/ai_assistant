"""
AI Code Assistant GUI with Toolbar Buttons and Icons
"""

import os
import json
import re
import requests
from PyQt5.QtWidgets import (
    QFileDialog, QApplication, QMainWindow, QPushButton,
    QTextEdit, QLabel, QVBoxLayout, QWidget, QMessageBox,
    QListWidget, QInputDialog, QProgressBar, QToolBar, QAction
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QSize

# Constants for file filtering and LLM API
FOLDER_PATH = "/mnt/c/Users/hjgkkghj/Documents/AI Assistant"
ALLOWED_EXTENSIONS = [".py", ".java", ".cpp", ".js", ".html", ".cs"]
LLM_API_URL = "http://localhost:11434/api/chat"


class CodeAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Code Assistant")
        self.setGeometry(100, 100, 800, 500)

        self._setup_ui()
        self._populate_file_list()

    def _setup_ui(self):
        """Initializes the layout and widgets."""
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        self.label = QLabel("Select a file:")
        self.file_list = QListWidget()
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # Add widgets to layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.file_list)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.result_box)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self._create_toolbar()

    def _create_toolbar(self):
        """Adds a toolbar with icon-based buttons."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))

        analyze_action = QAction(QIcon.fromTheme("system-search"), "Analyze", self)
        edit_action = QAction(QIcon.fromTheme("document-edit"), "Edit", self)
        browse_action = QAction(QIcon.fromTheme("folder-open"), "Browse", self)

        analyze_action.triggered.connect(self._analyze_file)
        edit_action.triggered.connect(self._edit_file)
        browse_action.triggered.connect(self._browse_files)

        toolbar.addAction(analyze_action)
        toolbar.addAction(edit_action)
        toolbar.addAction(browse_action)

        self.addToolBar(toolbar)

    def _populate_file_list(self):
        """Lists allowed files in the directory."""
        self.file_list.clear()
        for root, _, files in os.walk(FOLDER_PATH):
            for file in files:
                if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    rel_path = os.path.relpath(os.path.join(root, file), FOLDER_PATH)
                    self.file_list.addItem(rel_path)

    def _browse_files(self):
        """Allows user to add files to list via file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open Files", FOLDER_PATH,
            "All Supported Files (*.py *.java *.cpp *.js *.html *.cs)"
        )
        for file_path in files:
            rel_path = os.path.relpath(file_path, FOLDER_PATH)
            if rel_path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                self.file_list.addItem(rel_path)
        if files:
            self.file_list.setCurrentRow(self.file_list.count() - 1)

    def _read_file_content(self, path):
        """Reads a file and returns its contents."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"❌ Error reading file: {e}"

    def _send_prompt_to_llm(self, prompt):
        """Sends prompt to LLM and streams the result."""
        try:
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            response = requests.post(LLM_API_URL, json={
                "model": "dolphin-mixtral:8x7b",
                "messages": [{"role": "user", "content": prompt}]
            }, stream=True)

            collected = ""
            for i, line in enumerate(response.iter_lines(), 1):
                if line:
                    try:
                        partial = json.loads(line.decode("utf-8"))
                        collected += partial.get("message", {}).get("content", "")
                        if i % 3 == 0:
                            self.progress_bar.setValue(min(100, int(i)))
                            QApplication.processEvents()
                    except json.JSONDecodeError:
                        continue

            self.progress_bar.setValue(100)
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
            return collected
        except Exception as e:
            return f"❌ LLM communication failed: {e}"

    def _analyze_file(self):
        """Triggers the analyze process for the selected file."""
        selected = self.file_list.currentItem()
        if selected:
            file_path = os.path.join(FOLDER_PATH, selected.text())
            content = self._read_file_content(file_path)
            instruction, ok = QInputDialog.getText(self, "Analysis Instruction", "What should I analyze?")
            if ok and instruction:
                prompt = (
                    "Analyze this file with the following instruction: " + instruction +
                    "\n\n```python\n" + content[:3000] + "\n```"
                )
                result = self._send_prompt_to_llm(prompt)
                self.result_box.setText(result)

    def _edit_file(self):
        """Triggers the edit process with a prompt."""
        selected = self.file_list.currentItem()
        if selected:
            file_path = os.path.join(FOLDER_PATH, selected.text())
            content = self._read_file_content(file_path)
            instruction, ok = QInputDialog.getText(self, "Edit Instruction", "Describe the changes:")
            if ok and instruction:
                prompt = (
                    "Apply this change: " + instruction + "\n\n"
                    "Original code:\n```python\n" + content[:3000] + "\n```"
                )
                result = self._send_prompt_to_llm(prompt)
                match = re.search(r"```(?:python)?\n(.*?)```", result, re.DOTALL)
                if match:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(match.group(1))
                    self.result_box.setText("✅ File updated successfully.")
                else:
                    self.result_box.setText("❌ No valid code block found in LLM response.")


def run_gui():
    """Entry point to launch the application."""
    app = QApplication([])
    app.setStyleSheet('''QWidget {
        background-color: #f2f2f2;
        font-family: "Segoe UI", sans-serif;
        font-size: 10pt;
    }
    QPushButton {
        background-color: #e0e0e0;
        border: 1px solid #ccc;
        border-radius: 2px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #d6d6d6;
    }
    QListWidget, QTextEdit {
        background-color: #ffffff;
        border: 1px solid #ccc;
        padding: 5px;
    }''')
    window = CodeAssistantGUI()
    window.show()
    app.exec_()


if __name__ == "__main__":
    run_gui()
