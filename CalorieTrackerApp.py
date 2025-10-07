import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import hashlib
import os

# Database Manager Class
class DatabaseManager:
    """Handles all interaction with the SQLite database for users and entries."""
    def __init__(self, db_name="calorie_tracker.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
        db_path = os.path.abspath(db_name)
        print("---------------------------------------------")
        print(f"Database connected and tables checked.")
        print(f"DATABASE FILE LOCATION: {db_path}")
        print("---------------------------------------------")

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, meal TEXT NOT NULL, calories INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))"
        )
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        hashed_pw = self.hash_password(password)
        self.cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, hashed_pw))
        user = self.cursor.fetchone()
        
        if user:
            return user[0]
        return None

    def save_entry(self, user_id, meal, calories):
        self.cursor.execute("INSERT INTO entries (user_id, meal, calories) VALUES (?, ?, ?)", 
                            (user_id, meal, calories))
        self.conn.commit()

    def load_entries(self, user_id):
        self.cursor.execute("SELECT meal, calories FROM entries WHERE user_id = ?", (user_id,))
        return [{'meal': row[0], 'calories': row[1]} for row in self.cursor.fetchall()]

#Authentication Class
class AuthWindow:
    """Handles the user login and registration interface."""
    def __init__(self, master, db, login_success_callback):
        self.master = master
        self.db = db
        self.login_success_callback = login_success_callback
        
        self.master.withdraw() 
        
        self.auth_win = tk.Toplevel(master)
        self.auth_win.title("Calorie Tracker - Login / Register")
        self.auth_win.geometry("500x450")
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

        if self.db.register_user(username, password):
            messagebox.showinfo("Success", "Registration successful! You can now log in.", parent=self.auth_win)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Registration Error", "Username already exists. Please choose a different one.", parent=self.auth_win)

#Main Class
class CalorieTrackerApp:
    """The main calorie counter GUI, displayed only after successful login."""

    def __init__(self, master):
        self.master = master
        self.db = DatabaseManager()
        self.current_user_id = None
        self.current_username = None
        AuthWindow(master, self.db, self.show_main_tracker)
        
    def show_main_tracker(self, user_id, username):
        self.current_user_id = user_id
        self.current_username = username
        self.common_meals = [
            "Chicken and Rice",
            "Oatmeal",
            "Protein Shake",
            "Scrambled Eggs",
            "Tuna Salad",
            "Pasta with Sauce",
            "Apple",
            "Banana"
        ]

        self.master.title(f"Calorie Counter - Logged in as: {username}")
        self.master.geometry("900x700") 
        self.master.config(bg="#f0f0f0")      
        self.master.grid_columnconfigure(0, weight=3) 
        self.master.grid_columnconfigure(1, weight=1) 
        self.master.grid_rowconfigure(0, weight=1)
        main_content_frame = tk.Frame(self.master, bg="#f0f0f0")
        main_content_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_rowconfigure(2, weight=1)
        user_label = tk.Label(main_content_frame, text=f"User: {username} | ID: {user_id}", bg="#e0e0e0", font=('Arial', 9, 'italic'))
        user_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="ew")
        input_frame = tk.Frame(main_content_frame, padx=15, pady=15, bg="#e0e0e0")
        input_frame.grid(row=1, column=0, padx=0, pady=10, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        tk.Label(input_frame, text="Meal/Item:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        
        self.meal_var = tk.StringVar() 
        self.meal_entry = ttk.Combobox(
            input_frame, 
            textvariable=self.meal_var, 
            values=self.common_meals, 
            state="normal", 
            width=30, 
            font=('Arial', 10)
        )
        self.meal_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Label(input_frame, text="Calories:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.calories_entry = tk.Entry(input_frame, width=30, font=('Arial', 10))
        self.calories_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.add_button = tk.Button(
            input_frame, 
            text="Add Entry", 
            command=self.add_entry, 
            bg="#4CAF50", 
            fg="white", 
            activebackground="#45a049", 
            font=('Arial', 11, 'bold')
        )
        self.add_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        display_frame = tk.Frame(main_content_frame, padx=15, pady=15, bg="#ffffff", relief=tk.GROOVE, bd=1)
        display_frame.grid(row=2, column=0, padx=0, pady=10, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(2, weight=1)

        self.total_label = tk.Label(
            display_frame, 
            text="Total Calories: 0 kcal", 
            font=('Arial', 16, 'bold'), 
            fg="#E65100",
            bg="#ffffff"
        )
        self.total_label.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        tk.Label(display_frame, text="--- Today's Entries ---", fg="#555555", bg="#ffffff", font=('Arial', 10)).grid(row=1, column=0, sticky='ew', pady=(0, 5))
        text_scroll_frame = tk.Frame(display_frame)
        text_scroll_frame.grid(row=2, column=0, sticky="nsew")
        text_scroll_frame.grid_rowconfigure(0, weight=1)
        text_scroll_frame.grid_columnconfigure(0, weight=1)
        scrollbar = tk.Scrollbar(text_scroll_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.entries_text = tk.Text(
            text_scroll_frame, 
            height=12, 
            bd=1, 
            relief="sunken", 
            wrap="word", 
            bg="#f9f9f9", 
            font=('Consolas', 10),
            yscrollcommand=scrollbar.set
        )
        self.entries_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.entries_text.yview)     
        self.entries_text.config(state=tk.DISABLED)
        sidebar_frame = tk.Frame(self.master, padx=10, pady=10, bg="#eaf3ff", relief=tk.RIDGE, bd=2)
        sidebar_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        tk.Label(sidebar_frame, text="🔥 Daily Exercise Goal 🔥", 
                 font=('Arial', 12, 'bold'), fg="#333333", bg="#eaf3ff").pack(fill='x', pady=(0, 10))
        
        recommendations = [
            ("Walk 30 min", "150 kcal"),
            ("1 hour Strength Training", "300 kcal"),
            ("20 min HIIT", "250 kcal"),
            ("Yoga or Stretching", "80 kcal"),
            ("Running 5k", "400 kcal"),
            ("Cycling (Moderate)", "350 kcal")
        ]
        
        for name, calories in recommendations:
            item_frame = tk.Frame(sidebar_frame, bg="#ffffff", padx=10, pady=8, relief=tk.FLAT)
            item_frame.pack(fill='x', pady=5)
            tk.Label(item_frame, text=name, font=('Arial', 10, 'bold'), bg="#ffffff", fg="#0056b3").pack(anchor='w')
            tk.Label(item_frame, text=f"Burn Est.: {calories}", font=('Arial', 9), bg="#ffffff", fg="#666666").pack(anchor='w')

        tk.Label(sidebar_frame, text="\nTip: Consistency is key!", 
                 font=('Arial', 10, 'italic'), fg="#555555", bg="#eaf3ff").pack(pady=(10, 0))

        self.update_display()


    def add_entry(self):
        meal = self.meal_var.get().strip()
        calories_str = self.calories_entry.get().strip()
        if not meal or not calories_str:
            messagebox.showerror("Input Error", "Please fill in both the meal and calorie fields.")
            return
        try:
            calories = int(calories_str)
            if calories <= 0:
                messagebox.showerror("Input Error", "Calories must be a positive whole number.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Calories must be a positive whole number.")
            return
        self.db.save_entry(self.current_user_id, meal, calories)

        self.meal_var.set("") 
        self.calories_entry.delete(0, tk.END)

        self.update_display()

    def update_display(self):
        current_entries = self.db.load_entries(self.current_user_id)
        total = sum(entry['calories'] for entry in current_entries)
        self.total_label.config(text=f"Total Calories: {total} kcal")
        self.entries_text.config(state=tk.NORMAL)
        self.entries_text.delete(1.0, tk.END)
        if not current_entries:
            self.entries_text.insert(tk.END, "No entries tracked yet. Add a meal above!")
        else:
            for entry in current_entries:
                line = f"{entry['meal']}: {entry['calories']} kcal\n"
                self.entries_text.insert(tk.END, line)
                
        self.entries_text.config(state=tk.DISABLED)
        
if __name__ == '__main__':
    root = tk.Tk()
    app = CalorieTrackerApp(root)
    root.mainloop()
