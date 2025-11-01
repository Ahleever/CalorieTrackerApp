import sqlite3
import hashlib
import os
from datetime import date, timedelta, datetime

class DatabaseManager:
    def __init__(self, db_name="calorie_tracker.db"):
        app_data_path = os.getenv('APPDATA')
        if not app_data_path:
            app_data_path = os.path.expanduser("~")
        self.app_dir = os.path.join(app_data_path, "CalorieTrackerApp")
        os.makedirs(self.app_dir, exist_ok=True)
        db_path = os.path.join(self.app_dir, db_name)
        self.conn = sqlite3.connect(db_name) 
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.ensure_date_column()
        self.create_default_admin() 
        
    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, age INTEGER, height INTEGER, weight REAL, goal_weight REAL, sex TEXT, activity_level TEXT)" 
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, meal TEXT NOT NULL, calories INTEGER NOT NULL, entry_date TEXT, FOREIGN KEY (user_id) REFERENCES users(id))" 
        )
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS WeightLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                weight_lb REAL NOT NULL,
                UNIQUE(user_id, log_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

    def ensure_date_column(self):
        self.cursor.execute("PRAGMA table_info(entries)")
        cols = [c[1] for c in self.cursor.fetchall()]
        if "entry_date" not in cols:
            self.cursor.execute("ALTER TABLE entries ADD COLUMN entry_date TEXT")
            self.conn.commit()

    def create_default_admin(self): 
        username = "demo"
        password = "password"
        
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_exists = self.cursor.fetchone()
        
        if user_exists:
            user_id = user_exists[0]
            if not self.load_weight_data(user_id):
                today = date.today()
                self.log_weight(user_id, 178.0, (today - timedelta(days=20)).isoformat())
                self.log_weight(user_id, 177.5, (today - timedelta(days=15)).isoformat())
                self.log_weight(user_id, 176.0, (today - timedelta(days=10)).isoformat())
                self.log_weight(user_id, 175.5, (today - timedelta(days=5)).isoformat())
                self.log_weight(user_id, 175.0, today.isoformat())
            return 
            
        user_id = self.register_user(username, password)
        if not user_id: return
        
        self.update_profile(
            user_id, 
            age=30, 
            height=70, 
            weight=175.0, 
            goal_weight=170.0, 
            sex='Male', 
            activity_level="Moderate (3-5 days/wk)"
        )
        
        today = date.today()
        
        day1 = today - timedelta(days=2)
        self.save_entry(user_id, "Oatmeal", 300, day1.isoformat())
        self.save_entry(user_id, "Chicken & Veggies", 750, day1.isoformat())
        self.save_entry(user_id, "Protein Shake", 200, day1.isoformat())
        
        day2 = today - timedelta(days=1)
        self.save_entry(user_id, "Scrambled Eggs", 450, day2.isoformat())
        self.save_entry(user_id, "Tuna Sandwich", 550, day2.isoformat())
        self.save_entry(user_id, "Pasta Dinner", 800, day2.isoformat())

        self.log_weight(user_id, 178.0, (today - timedelta(days=20)).isoformat())
        self.log_weight(user_id, 177.5, (today - timedelta(days=15)).isoformat())
        self.log_weight(user_id, 176.0, (today - timedelta(days=10)).isoformat())
        self.log_weight(user_id, 175.5, (today - timedelta(days=5)).isoformat())
        self.log_weight(user_id, 175.0, today.isoformat())
        
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        hashed_pw = self.hash_password(password)
        self.cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, hashed_pw))
        user = self.cursor.fetchone()
        
        if user:
            return user[0]
        return None

    def update_profile(self, user_id, age, height, weight, goal_weight, sex, activity_level):
        self.cursor.execute(
            "UPDATE users SET age=?, height=?, weight=?, goal_weight=?, sex=?, activity_level=? WHERE id=?",
            (age, height, weight, goal_weight, sex, activity_level, user_id)
        )
        self.conn.commit()

    def get_user_profile(self, user_id):
        self.cursor.execute("SELECT age, height, weight, goal_weight, sex, activity_level FROM users WHERE id=?", (user_id,))
        return self.cursor.fetchone()
    
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

    def load_tracked_dates(self, user_id): 
        self.cursor.execute(                   
            "SELECT DISTINCT entry_date FROM entries WHERE user_id = ? AND entry_date IS NOT NULL", 
            (user_id,)                         
        )                                    
        return [row[0] for row in self.cursor.fetchall()] 

    def log_weight(self, user_id, weight_lb, log_date=None):
        """Logs a new weight (in Lbs) for a specific date (or today)."""
        if log_date is None:
            log_date = date.today().isoformat()
            
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO WeightLogs (user_id, log_date, weight_lb)
                VALUES (?, ?, ?)
            """, (user_id, log_date, float(weight_lb)))
            self.conn.commit()
            self.cursor.execute("UPDATE users SET weight=? WHERE id=?", (float(weight_lb), user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error logging weight: {e}")
            return False

    def load_weight_data(self, user_id):
        self.cursor.execute("""
            SELECT log_date, weight_lb FROM WeightLogs 
            WHERE user_id = ?
            ORDER BY log_date ASC
        """, (user_id,))
        return self.cursor.fetchall()