import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import hashlib
import os
from datetime import date, timedelta
try:
    from tkcalendar import DateEntry
except Exception:
    DateEntry = None

# Database Manager Class
class DatabaseManager:
    def __init__(self, db_name="calorie_tracker.db"):
        self.conn = sqlite3.connect(db_name) 
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.ensure_date_column()
        
    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, meal TEXT NOT NULL, calories INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))"
        )
        self.conn.commit()

    def ensure_date_column(self):
        self.cursor.execute("PRAGMA table_info(entries)")
        cols = [c[1] for c in self.cursor.fetchall()]
        if "entry_date" not in cols:
            self.cursor.execute("ALTER TABLE entries ADD COLUMN entry_date TEXT")
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

    def save_entry(self, user_id, meal, calories, entry_date=None):
        if entry_date is None:
            entry_date = date.today().isoformat()
        self.cursor.execute(
            "INSERT INTO entries (user_id, meal, calories, entry_date) VALUES (?, ?, ?, ?)",
            (user_id, meal, calories, entry_date)
        )
        self.conn.commit()

    def load_entries(self, user_id, entry_date=None):
        if entry_date is None:
            entry_date = date.today().isoformat()
        self.cursor.execute(
            "SELECT meal, calories FROM entries WHERE user_id = ? AND entry_date = ?",
            (user_id, entry_date)
        )
        return [{'meal': row[0], 'calories': row[1]} for row in self.cursor.fetchall()]

    def load_daily_totals(self, user_id, limit=30):
        self.cursor.execute(
            """
            SELECT entry_date, SUM(calories) as total
            FROM entries
            WHERE user_id = ?
            GROUP BY entry_date
            ORDER BY entry_date DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        return [{'date': row[0], 'total': row[1]} for row in self.cursor.fetchall()]

# Authentication Window Class
class AuthWindow:
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


# Main Application Class
class CalorieTrackerApp:
    def __init__(self, master):
        self.master = master
        self.db = DatabaseManager()
        self.current_user_id = None
        self.current_username = None

        self.show_auth_window()

    def show_auth_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        AuthWindow(self.master, self.db, self.show_main_tracker)
    
    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.master.title("Calorie Counter")
        self.master.geometry("200x200")
        self.show_auth_window()

    def change_day(self, delta_days):
        self.selected_date = self.selected_date + timedelta(days=delta_days)
        if hasattr(self, "date_label_var"):
            self.date_label_var.set(self.selected_date.isoformat())
        if hasattr(self, "date_picker") and self.date_picker is not None:
            self.date_picker.set_date(self.selected_date)
        self.update_display()

    def show_main_tracker(self, user_id, username):
        self.current_user_id = user_id
        self.current_username = username
        self.selected_date = date.today()
        
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

        for widget in self.master.winfo_children():
            widget.destroy()

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

        #Header for User Info and Logout Button
        header_frame = tk.Frame(main_content_frame, bg="#e0e0e0")
        header_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        user_label = tk.Label(header_frame, text=f"User: {username} | ID: {user_id}", bg="#e0e0e0", font=('Arial', 9, 'italic'))
        user_label.grid(row=0, column=0, sticky="w", padx=5)

        tk.Button(header_frame, text="Logout", command=self.logout, 
                  bg="#dc3545", fg="white", activebackground="#c82333", font=('Arial', 9, 'bold')).grid(row=0, column=1, sticky="e", padx=5)

        input_frame = tk.Frame(main_content_frame, padx=15, pady=15, bg="#e0e0e0")
        input_frame.grid(row=1, column=0, padx=0, pady=10, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        
        date_row = 0
        date_frame = tk.Frame(input_frame, bg="#e0e0e0")
        date_frame.grid(row=date_row, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        date_frame.grid_columnconfigure(0, weight=1)
        date_frame.grid_columnconfigure(2, weight=1)
        date_frame.grid_columnconfigure(3, weight=1)

        tk.Label(date_frame, text="Date:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=(0,8))
        
        tk.Button(date_frame, text="◀ Prev", command=lambda: self.change_day(-1)).grid(row=0, column=1, sticky="w")
        
        if DateEntry is not None:
            self.date_picker = DateEntry(date_frame, width=12, background='darkblue', foreground='white',
                                         borderwidth=2, date_pattern="yyyy-mm-dd")
            self.date_picker.set_date(self.selected_date)
            self.date_picker.grid(row=0, column=2, padx=12)
            def _on_date_change(*_):
                self.selected_date = self.date_picker.get_date()
                self.update_display()
            self.date_picker.bind("<<DateEntrySelected>>", lambda e: _on_date_change())
        else:
            self.date_label_var = tk.StringVar(value=self.selected_date.isoformat())
            tk.Label(date_frame, textvariable=self.date_label_var, bg="#e0e0e0", font=('Arial', 10)).grid(row=0, column=2, padx=8)
            
        tk.Button(date_frame, text="Next ▶", command=lambda: self.change_day(1)).grid(row=0, column=3, sticky="w")
            
        tk.Label(input_frame, text="Meal/Item:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        
        self.meal_var = tk.StringVar()
        self.meal_entry = ttk.Combobox(
            input_frame, 
            textvariable=self.meal_var, 
            values=self.common_meals,
            state="normal",
            width=30, 
            font=('Arial', 10)
        )
        self.meal_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(input_frame, text="Calories:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.calories_entry = tk.Entry(input_frame, width=30, font=('Arial', 10))
        self.calories_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.add_button = tk.Button(
            input_frame, 
            text="Add Entry", 
            command=self.add_entry, 
            bg="#4CAF50", 
            fg="white", 
            activebackground="#45a049", 
            font=('Arial', 11, 'bold')
        )
        self.add_button.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

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

        tk.Label(display_frame, text="--- Entries ---", fg="#555555", bg="#ffffff", font=('Arial', 10)).grid(row=1, column=0, sticky='ew', pady=(0, 5))
        
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

        # Exercise Sidebar
        sidebar_frame = tk.Frame(self.master, padx=10, pady=10, bg="#eaf3ff", relief=tk.RIDGE, bd=2)
        sidebar_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        recommendations = [
            ("Walk 30 min", "150 kcal"),
            ("1 hour Strength Training", "300 kcal"),
            ("20 min HIIT", "250 kcal"),
            ("Yoga or Stretching", "80 kcal"),
            ("Running 5k", "400 kcal"),
            ("Cycling (Moderate)", "350 kcal")
        ]
        sidebar_frame.grid_rowconfigure(len(recommendations)+4, weight=1)

        tk.Label(sidebar_frame, text="🔥 Daily Exercise Goal 🔥", 
                 font=('Arial', 12, 'bold'), fg="#333333", bg="#eaf3ff").grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        for i, (name, calories) in enumerate(recommendations):
            item_frame = tk.Frame(sidebar_frame, bg="#ffffff", padx=10, pady=8, relief=tk.FLAT)
            item_frame.grid(row=i+1, column=0, sticky='ew', pady=2)
            tk.Label(item_frame, text=name, font=('Arial', 10, 'bold'), bg="#ffffff", fg="#0056b3").pack(anchor='w')
            tk.Label(item_frame, text=f"Burn Est.: {calories}", font=('Arial', 9), bg="#ffffff", fg="#666666").pack(anchor='w')

        tk.Label(sidebar_frame, text="\nTip: Consistency is key!", 
                 font=('Arial', 10, 'italic'), fg="#555555", bg="#eaf3ff").grid(row=len(recommendations)+1, column=0, sticky='ew', pady=(10, 0))

        # History section 
        hist_title = tk.Label(sidebar_frame, text="\n📅 Recent Daily Totals", 
                             font=('Arial', 12, 'bold'), fg="#333333", bg="#eaf3ff")
        hist_title.grid(row=len(recommendations)+2, column=0, sticky='ew', pady=(16, 6))

        hist_container = tk.Frame(sidebar_frame, bg="#eaf3ff")
        hist_container.grid(row=len(recommendations)+3, column=0, sticky="nsew")
        hist_container.grid_rowconfigure(0, weight=1)
        hist_container.grid_columnconfigure(0, weight=1)

        self.history_list = tk.Listbox(hist_container, height=10)
        self.history_list.grid(row=0, column=0, sticky="nsew")

        def refresh_history():
            self.history_list.delete(0, tk.END)
            for row in self.db.load_daily_totals(self.current_user_id, limit=30):
                marker = " ←" if row['date'] == self.selected_date.isoformat() else ""
                self.history_list.insert(tk.END, f"{row['date']}: {row['total']} kcal{marker}")

        self.refresh_history = refresh_history

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

        self.db.save_entry(self.current_user_id, meal, calories, self.selected_date.isoformat())

        self.meal_var.set("")
        self.calories_entry.delete(0, tk.END)

        self.update_display()

    def update_display(self):
        current_entries = self.db.load_entries(self.current_user_id, self.selected_date.isoformat())
        
        total = sum(entry['calories'] for entry in current_entries)
        self.total_label.config(text=f"Total Calories on {self.selected_date.strftime('%b %d, %Y')}: {total} kcal")

        self.entries_text.config(state=tk.NORMAL)
        self.entries_text.delete(1.0, tk.END)
        
        if not current_entries:
            self.entries_text.insert(tk.END, f"No entries tracked for {self.selected_date.strftime('%A')}. Add a meal above!")
        else:
            for entry in current_entries:
                line = f"{entry['meal']}: {entry['calories']} kcal\n"
                self.entries_text.insert(tk.END, line)
                
        self.entries_text.config(state=tk.DISABLED)

        if hasattr(self, "refresh_history"):
            self.refresh_history()
        
# Run Application
if __name__ == '__main__':
    root = tk.Tk()
    app = CalorieTrackerApp(root)
    root.mainloop()
