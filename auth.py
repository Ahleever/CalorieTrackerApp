import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from utils import ProfileCalculator

class ProfileSetupWindow:
    def __init__(self, master, db, user_id, username, login_success_callback):
        self.master = master
        self.db = db
        self.user_id = user_id
        self.username = username
        self.login_success_callback = login_success_callback
        self.profile_win = ctk.CTkToplevel(master)
        self.profile_win.title("Setup Profile")
        
        win_width = 450
        win_height = 550
        screen_width = self.profile_win.winfo_screenwidth()
        screen_height = self.profile_win.winfo_screenheight()
        x_coord = int((screen_width / 2) - (win_width / 2))
        y_coord = int((screen_height / 2) - (win_height / 2))
        self.profile_win.geometry(f"{win_width}x{win_height}+{x_coord}+{y_coord}")

        self.profile_win.resizable(False, False)
        self.profile_win.protocol("WM_DELETE_WINDOW", self.on_close) 

        self.profile_win.grid_rowconfigure(0, weight=1)
        self.profile_win.grid_columnconfigure(0, weight=1)

        profile_frame = ctk.CTkFrame(
            self.profile_win, 
            corner_radius=15, 
            border_width=2,
            fg_color=("gray90", "gray15")
        )
        profile_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        profile_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            profile_frame, 
            text="Set Up Your Fitness Profile", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=(20, 20), sticky="n")

        self.entries = {}

        ctk.CTkLabel(profile_frame, text="Age (Years):", font=('Arial', 11)).grid(row=1, column=0, sticky="w", pady=5, padx=(20, 10))
        self.age_entry = ctk.CTkEntry(profile_frame, width=20, font=('Arial', 11))
        self.age_entry.grid(row=1, column=1, pady=5, padx=(0, 20), sticky="ew")
        self.entries["Age (Years):"] = self.age_entry # Store for save_profile logic

        ctk.CTkLabel(profile_frame, text="Height:", font=('Arial', 11)).grid(row=2, column=0, sticky="w", pady=5, padx=(20, 10))
        height_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        height_frame.grid(row=2, column=1, sticky="ew", padx=(0, 20)) 
        
        self.feet_entry = ctk.CTkEntry(height_frame, width=4, font=('Arial', 11), placeholder_text="Feet")
        self.feet_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        ctk.CTkLabel(height_frame, text=" ft ", fg_color="transparent", font=('Arial', 11)).pack(side=ctk.LEFT)
        
        self.inches_entry = ctk.CTkEntry(height_frame, width=4, font=('Arial', 11), placeholder_text="Inches")
        self.inches_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        ctk.CTkLabel(height_frame, text=" in ", fg_color="transparent", font=('Arial', 11)).pack(side=ctk.LEFT)

        ctk.CTkLabel(profile_frame, text="Current Weight (Lbs):", font=('Arial', 11)).grid(row=3, column=0, sticky="w", pady=5, padx=(20, 10))
        self.weight_entry = ctk.CTkEntry(profile_frame, width=20, font=('Arial', 11))
        self.weight_entry.grid(row=3, column=1, pady=5, padx=(0, 20), sticky="ew")
        self.entries["Current Weight (Lbs):"] = self.weight_entry

        ctk.CTkLabel(profile_frame, text="Goal Weight (Lbs):", font=('Arial', 11)).grid(row=4, column=0, sticky="w", pady=5, padx=(20, 10))
        self.goal_entry = ctk.CTkEntry(profile_frame, width=20, font=('Arial', 11))
        self.goal_entry.grid(row=4, column=1, pady=5, padx=(0, 20), sticky="ew")
        self.entries["Goal Weight (Lbs):"] = self.goal_entry
        
        ctk.CTkLabel(profile_frame, text="Sex:", font=('Arial', 11)).grid(row=5, column=0, sticky="w", pady=5, padx=(20, 10))
        self.sex_var = ctk.StringVar(value='Female')
        self.sex_combo = ctk.CTkComboBox(profile_frame, variable=self.sex_var, values=['Female', 'Male'], state='readonly', width=20, font=('Arial', 11))
        self.sex_combo.grid(row=5, column=1, pady=5, padx=(0, 20), sticky="ew")
        
        ctk.CTkLabel(profile_frame, text="Activity Level:", font=('Arial', 11)).grid(row=6, column=0, sticky="w", pady=5, padx=(20, 10))
        self.activity_var = ctk.StringVar(value=list(ProfileCalculator.ACTIVITY_FACTORS.keys())[0])
        self.activity_combo = ctk.CTkComboBox(profile_frame, variable=self.activity_var, values=list(ProfileCalculator.ACTIVITY_FACTORS.keys()), state='readonly', width=20, font=('Arial', 11))
        self.activity_combo.grid(row=6, column=1, pady=5, padx=(0, 20), sticky="ew")
        
        self.save_btn = ctk.CTkButton(
            profile_frame, 
            text="Save & Start Tracking", 
            command=self.save_profile, 
            fg_color="#28a745", 
            hover_color="#1e7e34",
            text_color="white", 
            font=('Arial', 12, 'bold'),
            height=40
        )
        self.save_btn.grid(row=7, column=0, columnspan=2, pady=(30, 20), padx=20, sticky="ew")
        self.profile_win.bind('<Return>', lambda event: self.save_profile())

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
        
        self.auth_win = ctk.CTkToplevel(master)
        self.auth_win.title("Calorie Tracker - Login / Register")
        
        win_width = 500
        win_height = 450
        screen_width = self.auth_win.winfo_screenwidth()
        screen_height = self.auth_win.winfo_screenheight()
        x_coord = int((screen_width / 2) - (win_width / 2))
        y_coord = int((screen_height / 2) - (win_height / 2))
        self.auth_win.geometry(f"{win_width}x{win_height}+{x_coord}+{y_coord}")
        
        self.auth_win.resizable(False, False)
        self.auth_win.grid_rowconfigure(0, weight=1)
        self.auth_win.grid_columnconfigure(0, weight=1)
        self.auth_win.protocol("WM_DELETE_WINDOW", self.on_close) 

        # Main Auth Frame
        auth_frame = ctk.CTkFrame(
            self.auth_win, 
            corner_radius=15,
            border_width=2
        )
        auth_frame.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        auth_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            auth_frame, 
            text="Welcome to the Tracker", 
            font=('Arial', 16, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=(25, 25), sticky="n")

        ctk.CTkLabel(auth_frame, text="Username:", font=('Arial', 12)).grid(row=1, column=0, sticky="w", pady=10, padx=(30, 10))
        self.username_entry = ctk.CTkEntry(auth_frame, width=30, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, padx=(0, 30), pady=10, sticky="ew")

        ctk.CTkLabel(auth_frame, text="Password:", font=('Arial', 12)).grid(row=2, column=0, sticky="w", pady=10, padx=(30, 10))
        self.password_entry = ctk.CTkEntry(auth_frame, width=30, show="*", font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, padx=(0, 30), pady=10, sticky="ew")

        self.auth_win.bind('<Return>', lambda event: self.login())

        ctk.CTkButton(
            auth_frame, 
            text="Login", 
            command=self.login, 
            fg_color="#007bff",
            hover_color="#0056b3",
            text_color="white", 
            font=('Arial', 12, 'bold'),
            height=35
        ).grid(row=3, column=0, columnspan=2, pady=(20, 10), padx=30, sticky="ew")
        
        self.register_btn = ctk.CTkButton(
            auth_frame, 
            text="Register New Account", 
            command=self.register, 
            fg_color="#28a745", 
            hover_color="#1e7e34",
            text_color="white", 
            font=('Arial', 12),
            height=35
        )
        self.register_btn.grid(row=4, column=0, columnspan=2, pady=(5, 30), padx=30, sticky="ew")
    
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
            ProfileSetupWindow(self.master, self.db, user_id, username, self.login_success_callback)
        else:
            messagebox.showerror("Registration Error", "Username already exists. Please choose a different one.", parent=self.auth_win)