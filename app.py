import tkinter as tk
from tkinter import messagebox
from datetime import date, timedelta
from database import DatabaseManager
from auth import AuthWindow
from ui_components import (ProfileDisplayFrame, InputFrame, 
                           EntriesDisplay, WeightGraph, SidebarFrame)

try:
    from tkcalendar import DateEntry 
except Exception:
    DateEntry = None

class CalorieTrackerApp:
    def __init__(self, master):
        self.master = master
        self.db = DatabaseManager()
        self.current_user_id = None
        self.current_username = None
        self.date_format = "%Y-%m-%d"
        self.selected_date = date.today()

        self.profile_display = None
        self.input_frame = None
        self.entries_display = None
        self.weight_graph = None
        self.sidebar = None

        self.show_auth_window()

    def show_auth_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        AuthWindow(self.master, self.db, self.on_login_success)
    
    def on_login_success(self, user_id, username):
        """Callback function for when login or profile setup is successful."""
        self.current_user_id = user_id
        self.current_username = username
        self.show_main_tracker()

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.master.title("Calorie Counter")
        self.master.geometry("200x200")
        self.show_auth_window()

    def change_day(self, delta_days):
        self.selected_date = self.selected_date + timedelta(days=delta_days)
        if self.input_frame:
            self.input_frame.update_date_picker(self.selected_date)
        self.update_all_displays()

    def set_date(self, new_date):
        """Called by the DateEntry widget when a new date is selected."""
        self.selected_date = new_date
        self.update_all_displays()

    def add_entry(self, meal, calories_str, weight_str):
        """Handles logic for adding a meal or logging weight."""
        calorie_logged = False
        weight_logged = False

        if meal and calories_str:
            try:
                calories = int(calories_str)
                if calories <= 0:
                    messagebox.showerror("Input Error", "Calories must be a positive whole number.")
                    return
                self.db.save_entry(self.current_user_id, meal, calories, self.selected_date.isoformat())
                calorie_logged = True
            except ValueError:
                messagebox.showerror("Input Error", "Calories must be a positive whole number.")
                return

        if weight_str:
            try:
                weight = float(weight_str)
                if weight <= 0:
                    messagebox.showerror("Input Error", "Weight must be a positive number.")
                    return
                
                if self.db.log_weight(self.current_user_id, weight, self.selected_date.isoformat()):
                    weight_logged = True
                
            except ValueError:
                messagebox.showerror("Input Error", "Weight must be a valid positive number.")
                return

        if not calorie_logged and not weight_logged:
            messagebox.showerror("Input Error", "Please enter a valid Meal/Calorie entry or a Weight value to save.")
            return

        if self.input_frame:
            self.input_frame.clear_inputs()

        self.update_all_displays()

    def highlight_tracked_dates(self):
        """Highlights dates with entries in the calendar."""
        if DateEntry is None or not self.input_frame or not self.input_frame.date_picker:
            return
        
        calendar_widget = self.input_frame.date_picker
        if not hasattr(calendar_widget, 'calevent_remove'):
            return

        calendar_widget.calevent_remove('all') 
        tracked_dates_str = self.db.load_tracked_dates(self.current_user_id) 
        
        calendar_widget.tag_config(
            'tracked_day', 
            background='#4CAF50', 
            foreground='white'  
        )
        
        for date_str in tracked_dates_str:
            try:
                d = date.fromisoformat(date_str)
                calendar_widget.calevent_configure(d, tags=('tracked_day',))
            except ValueError:
                continue

    def update_all_displays(self):
        """A single method to refresh all UI components."""
        if self.current_user_id is None:
            return

        if self.profile_display:
            profile_data = self.db.get_user_profile(self.current_user_id)
            self.profile_display.update_metrics(profile_data)

        if self.entries_display:
            current_entries = self.db.load_entries(self.current_user_id, self.selected_date.isoformat())
            weight_data = self.db.load_weight_data(self.current_user_id)
            self.entries_display.update_entries(current_entries, weight_data, self.selected_date)

        if self.weight_graph:
            weight_data = self.db.load_weight_data(self.current_user_id)
            self.weight_graph.plot(weight_data)

        if self.sidebar:
            daily_totals = self.db.load_daily_totals(self.current_user_id, limit=30)
            self.sidebar.refresh_history(daily_totals, self.selected_date)
        
        self.highlight_tracked_dates()

    def show_main_tracker(self):
        self.master.state('zoomed')
        self.selected_date = date.today()

        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.title(f"Calorie Counter - Logged in as: {self.current_username}")
        self.master.minsize(1000, 1000) 
        self.master.config(bg="#f0f0f0")
        
        self.master.grid_columnconfigure(0, weight=3) 
        self.master.grid_columnconfigure(1, weight=1) 
        self.master.grid_rowconfigure(0, weight=1)    
        
        #Main Content Frame 
        main_content_frame = tk.Frame(self.master, bg="#f0f0f0")
        main_content_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_rowconfigure(2, weight=1) # Make display_frame grow

        # Header
        header_frame = tk.Frame(main_content_frame, bg="#e0e0e0")
        header_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(header_frame, text=f"User: {self.current_username} | ID: {self.current_user_id}", bg="#e0e0e0", font=('Arial', 9, 'italic')).grid(row=0, column=0, sticky="w", padx=5)
        tk.Button(header_frame, text="Logout", command=self.logout, 
                  bg="#dc3545", fg="white", activebackground="#c82333", font=('Arial', 9, 'bold')).grid(row=0, column=1, sticky="e", padx=5)

        # Top Frame
        top_horizontal_frame = tk.Frame(main_content_frame, bg="#f0f0f0")
        top_horizontal_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        top_horizontal_frame.grid_columnconfigure(0, weight=1) 
        top_horizontal_frame.grid_columnconfigure(1, weight=1) 

        # Profile Display Component
        self.profile_display = ProfileDisplayFrame(top_horizontal_frame, relief=tk.GROOVE, bd=1)
        self.profile_display.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        
        # Input Frame Component
        self.input_frame = InputFrame(top_horizontal_frame, self, relief=tk.GROOVE, bd=1)
        self.input_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        self.input_frame.update_date_picker(self.selected_date)

        #Main Display Frame (Entries and Graph) 
        display_frame = tk.Frame(main_content_frame, padx=15, pady=15, bg="#ffffff", relief=tk.GROOVE, bd=1)
        display_frame.grid(row=2, column=0, padx=0, pady=10, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(1, weight=1) 
        display_frame.grid_rowconfigure(3, weight=1) 

        #Entries Display 
        self.entries_display = EntriesDisplay(display_frame)
        self.entries_display.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        #Graph Component
        self.weight_graph = WeightGraph(display_frame)
        self.weight_graph.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        #Sidebar Frame
        self.sidebar = SidebarFrame(self.master)
        self.sidebar.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        self.update_all_displays()