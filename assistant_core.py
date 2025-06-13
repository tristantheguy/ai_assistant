# core_assistant.py

import os
import subprocess
import datetime

class AIAssistant:
    def __init__(self):
        self.greeting()

    def greeting(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🤖 Hello! AI Assistant ready. Current time: {now}\n")

    def run(self):
        while True:
            user_input = input(">>> ").strip()
            if user_input.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break
            elif user_input.startswith("!"):
                self.run_shell_command(user_input[1:])
            elif user_input.lower().startswith("read "):
                self.read_file(user_input[5:].strip())
            else:
                print("❓ Unknown command. Try `!cmd`, `read <filepath>`, or `exit`.")

    def run_shell_command(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            print(f"$ {cmd}\n{result.stdout}")
            if result.stderr:
                print(f"⚠️ {result.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def read_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                print(f.read())
        except FileNotFoundError:
            print("❌ File not found.")
        except Exception as e:
            print(f"❌ Error reading file: {e}")

if __name__ == '__main__':
    assistant = AIAssistant()
    assistant.run()
