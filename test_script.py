import time
import tkinter as tk

def hello():
    win = tk.Tk()
    win.title("Sad PopUp")

    # Change background color to blue
    win.configure(bg='blue')

    label = tk.Label(win, text=":'(", bg='blue', fg='white')
    label.pack()

    def close_program():
        win.destroy()

    button = tk.Button(win, text="Click me!", command=close_program)
    button.configure(bg='blue', fg='white')  # Change button colors to white text on blue background
    button.pack()

    label.after(5000, close_program)  # Destroy the window after 5 seconds (5000 milliseconds)
    win.mainloop()

hello()
