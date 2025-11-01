import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
from utils import ProfileCalculator

class ProfileSetupWindow:
    def __init__(self, master, db, user_id, username, login_success_callback):
        self.master = master
        self.db = db
        self.user_id = user_id
        self.username = username
        self.login_success_callback = login_success_callback
        
        self.profile_win = tk.Toplevel(master)
        self.profile_win.title("Setup Profile")
        self.profile_win.geometry("450x550")
        self.profile_win.config(bg="#f9f9f9")
        self.profile_win.resizable(False, False)
        self.profile_win.protocol("WM_DELETE_WINDOW", self.on_close) 

        self.profile_win.grid_rowconfigure(0, weight=1)
        self.profile_win.grid_columnconfigure(0, weight=1)

        profile_frame = tk.Frame(self.profile_win, padx=20, pady=20, bg="#e0e0e0", relief=tk.RAISED, bd=2)
        profile_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        profile_frame.grid_columnconfigure(1, weight=1)

        tk.Label(profile_frame, text="Set Up Your Fitness Profile", bg="#e0e0e0", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="n")

        #Input Fields
        fields = [
            ("Age (Years):", 1),
            ("Current Weight (Lbs):", 3),
            ("Goal Weight (Lbs):", 4),
        ]
        self.entries = {}

        for i, (text, row) in enumerate(fields):
            tk.Label(profile_frame, text=text, bg="#e0e0e0", font=('Arial', 11)).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            entry = tk.Entry(profile_frame, width=20, font=('Arial', 11))
            entry.grid(row=row, column=1, pady=5, sticky="ew")
            self.entries[text] = entry
        tk.Label(profile_frame, text="Height:", bg="#e0e0e0", font=('Arial', 11)).grid(row=2, column=0, sticky="w", pady=5, padx=(0, 10))
        height_frame = tk.Frame(profile_frame, bg="#e0e0e0")
        height_frame.grid(row=2, column=1, sticky="ew")  
        self.feet_entry = tk.Entry(height_frame, width=4, font=('Arial', 11))
        self.feet_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(height_frame, text=" ft ", bg="#e0e0e0", font=('Arial', 11)).pack(side=tk.LEFT)
        self.inches_entry = tk.Entry(height_frame, width=4, font=('Arial', 11))
        self.inches_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(height_frame, text=" in ", bg="#e0e0e0", font=('Arial', 11)).pack(side=tk.LEFT)
        tk.Label(profile_frame, text="Sex:", bg="#e0e0e0", font=('Arial', 11)).grid(row=5, column=0, sticky="w", pady=5, padx=(0, 10))
        self.sex_var = tk.StringVar(value='Female')
        self.sex_combo = ttk.Combobox(profile_frame, textvariable=self.sex_var, values=['Female', 'Male'], state='readonly', width=20, font=('Arial', 11))
        self.sex_combo.grid(row=5, column=1, pady=5, sticky="ew")
        tk.Label(profile_frame, text="Activity Level:", bg="#e0e0e0", font=('Arial', 11)).grid(row=6, column=0, sticky="w", pady=5, padx=(0, 10))
        self.activity_var = tk.StringVar(value=ProfileCalculator.ACTIVITY_FACTORS.keys().__iter__().__next__())
        self.activity_combo = ttk.Combobox(profile_frame, textvariable=self.activity_var, values=list(ProfileCalculator.ACTIVITY_FACTORS.keys()), state='readonly', width=20, font=('Arial', 11))
        self.activity_combo.grid(row=6, column=1, pady=5, sticky="ew")
        tk.Button(profile_frame, text="Save & Start Tracking", command=self.save_profile, bg="#28a745", fg="white", font=('Arial', 12, 'bold')).grid(row=7, column=0, columnspan=2, pady=(30, 0), sticky="ew", ipady=8)

    def on_close(self):
        messagebox.showwarning("Warning", "You must save your profile to start tracking.", parent=self.profile_win)

    def save_profile(self):
        try:
            age = int(self.entries["Age (Years):"].get())
            feet = int(self.feet_entry.get())
            inches = int(self.inches_entry.get())
            height_total_inches = (feet * 12) + inches
            weight = float(self.entries["Current Weight (Lbs):"].get())
            goal_weight = float(self.entries["Goal Weight (Lbs):"].get())
            sex = self.sex_var.get()
            activity_level = self.activity_var.get()

            if age <= 0 or height_total_inches <= 0 or weight <= 0 or goal_weight <= 0:
                 raise ValueError("All values must be positive.")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid positive numbers for all fields. {e}", parent=self.profile_win)
            return

        self.db.update_profile(self.user_id, age, height_total_inches, weight, goal_weight, sex, activity_level)
        
        self.db.log_weight(self.user_id, weight, date.today().isoformat())
        
        self.profile_win.destroy()
        self.login_success_callback(self.user_id, self.username) 

class AuthWindow:
    def __init__(self, master, db, login_success_callback):
        self.master = master
        self.db = db
        self.login_success_callback = login_success_callback
        
        self.master.withdraw() 
        
        self.auth_win = tk.Toplevel(master)
        self.auth_win.title("Calorie Tracker - Login / Register")
        win_width = 500
        win_height = 450
        screen_width = self.auth_win.winfo_screenwidth()
        screen_height = self.auth_win.winfo_screenheight()
        x_coord = int((screen_width / 2) - (win_width / 2))
        y_coord = int((screen_height / 2) - (win_height / 2))
        self.auth_win.geometry(f"{win_width}x{win_height}+{x_coord}+{y_coord}")
        self.auth_win.config(bg="#f9f9f9")
        self.auth_win.resizable(False, False)
        
        self.auth_win.grid_rowconfigure(0, weight=1)
        self.auth_win.grid_columnconfigure(0, weight=1)

        self.auth_win.protocol("WM_DELETE_WINDOW", self.on_close) 

        auth_frame = tk.Frame(self.auth_win, padx=30, pady=30, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        auth_frame.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        auth_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(auth_frame, text="Welcome to the Tracker", bg="#f0f0f0", font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 25), sticky="n")

        tk.Label(auth_frame, text="Username:", bg="#f0f0f0", font=('Arial', 12)).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))
        self.username_entry = tk.Entry(auth_frame, width=30, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        tk.Label(auth_frame, text="Password:", bg="#f0f0f0", font=('Arial', 12)).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))
        self.password_entry = tk.Entry(auth_frame, width=30, show="*", font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        tk.Button(auth_frame, text="Login", command=self.login, bg="#007bff", fg="white", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=2, pady=(20, 10), sticky="ew", ipady=5)
        tk.Button(auth_frame, text="Register New Account", command=self.register, bg="#28a745", fg="white", font=('Arial', 12)).grid(row=4, column=0, columnspan=2, pady=(5, 0), sticky="ew", ipady=5)
    
    def on_close(self):
        self.master.destroy()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password.", parent=self.auth_win)
            return
        
        user_id = self.db.login_user(username, password)
        
        if user_id:
            self.auth_win.destroy()
            self.master.deiconify()
            self.login_success_callback(user_id, username)
        else:
            messagebox.showerror("Login Error", "Invalid username or password.", parent=self.auth_win)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if len(password) < 4:
            messagebox.showerror("Registration Error", "Password must be at least 4 characters.", parent=self.auth_win)
            return

        user_id = self.db.register_user(username, password)

        if user_id:
            self.auth_win.destroy()
            self.master.deiconify() 
            ProfileSetupWindow(self.master, self.db, user_id, username, self.login_success_callback)
        else:
            messagebox.showerror("Registration Error", "Username already exists. Please choose a different one.", parent=self.auth_win)