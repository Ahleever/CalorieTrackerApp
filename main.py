import tkinter as tk
from app import CalorieTrackerApp
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    root = tk.Tk()
    try:
        icon_path = resource_path("my_icon.ico")
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Error setting icon: {e}")
    app = CalorieTrackerApp(root)
    root.mainloop()