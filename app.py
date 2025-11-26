import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta
from database import DatabaseManager
from auth import AuthWindow
from ui_components import (ProfileDisplayFrame, InputFrame, 
                           EntriesDisplay, WeightGraph, SidebarFrame, FoodPickDialog)
from utils import ProfileCalculator
import urllib.parse
import urllib.request
import json
import os

try:
    from tkcalendar import DateEntry 
except Exception:
    DateEntry = None

class FoodAPI:
    FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
    DEFAULT_API_KEY = "Ql50Qs6lFfizUbEredHizw6FHlcr2FcBMoNlr6Zu" 

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else self.DEFAULT_API_KEY

    def _http_get_json(self, url, params, timeout=10):
        qs = urllib.parse.urlencode(params)
        full = f"{url}?{qs}"
        with urllib.request.urlopen(full, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search_kcal_per_100g(self, query, page_size=12):
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": "Foundation,SR Legacy"
        }
        try:
            js = self._http_get_json(self.FDC_SEARCH_URL, params)
        except Exception as e:
            print(f"API Error: {e}")
            return []
            
        foods = js.get("foods", []) or []
        out = []
        for f in foods:
            kcal = None
            for n in f.get("foodNutrients", []) or []:
                if str(n.get("nutrientId")) == "1008": 
                    kcal = n.get("value")
                    break
                name = (n.get("nutrientName") or "").lower()
                unit = (n.get("unitName") or "").lower()
                if name == "energy" and "kcal" in unit:
                    kcal = n.get("value")
                    break
            if kcal is None:
                continue
            try:
                kcal = float(kcal)
            except Exception:
                continue
            out.append({
                "fdcId": f.get("fdcId"),
                "description": (f.get("description") or "").strip(),
                "dataType": f.get("dataType"),
                "kcal_100g": kcal
            })
        return out


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
        
        api_key = os.environ.get("FDC_API_KEY")
        self.food_api = FoodAPI(api_key)
        
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("green")
        
        self.show_auth_window()

    def show_auth_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        AuthWindow(self.master, self.db, self.on_login_success)
    
    def on_login_success(self, user_id, username):
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
        self.selected_date = new_date
        self.update_all_displays()

    def add_entry(self, meal, calories_str, weight_str):
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

    def find_and_add_from_api(self):
        query = self.input_frame.api_food_var.get().strip()
        grams_str = self.input_frame.api_grams_var.get().strip()
        
        if not query:
            messagebox.showerror("Missing Input", "Please type a food name to search.")
            return
        
        try:
            grams = float(grams_str)
            if grams <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Grams must be a positive number.")
            return

        try:
            results = self.food_api.search_kcal_per_100g(query)
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to connect to USDA API.\n{e}")
            return

        if not results:
            messagebox.showinfo("No Results", "No matches found for that food.")
            return

        def on_food_picked(item):
            kcal_per_100g = item['kcal_100g']
            total_kcal = int(round(kcal_per_100g * (grams / 100.0)))
            description = f"{item['description']} ({int(grams)}g)"
            
            self.db.save_entry(self.current_user_id, description, total_kcal, self.selected_date.isoformat())
            
            self.input_frame.clear_inputs()
            self.update_all_displays()
            messagebox.showinfo("Success", f"Added: {description}\nCalories: {total_kcal}")

        FoodPickDialog(self.master, results, on_food_picked)

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
            background='#2ECC71',
            foreground='white'    
        )
        
        for date_str in tracked_dates_str:
            try:
                d = date.fromisoformat(date_str)
                calendar_widget.calevent_configure(d, tags=('tracked_day',))
            except ValueError:
                continue

    def update_all_displays(self):
        if self.current_user_id is None:
            return

        profile_data = self.db.get_user_profile(self.current_user_id)
        current_entries = self.db.load_entries(self.current_user_id, self.selected_date.isoformat())
        current_total_cals = sum(entry['calories'] for entry in current_entries)

        if self.profile_display:
            self.profile_display.update_metrics(profile_data)

        if self.entries_display:
            weight_data = self.db.load_weight_data(self.current_user_id)
            self.entries_display.update_entries(current_entries, weight_data, self.selected_date)

        if self.weight_graph:
            weight_data = self.db.load_weight_data(self.current_user_id)
            self.weight_graph.plot(weight_data)

        if self.sidebar:
            daily_totals = self.db.load_daily_totals(self.current_user_id, limit=30)
            self.sidebar.refresh_history(daily_totals, self.selected_date)
            
            if profile_data and not any(x is None for x in profile_data):
                try:
                    age, height_in, weight_lb, goal_weight_lb, sex, activity_level = profile_data
                    calc = ProfileCalculator(age, height_in, weight_lb, sex, activity_level)
                    bmr = calc.calculate_bmr()
                    tdee_maintenance = calc.calculate_tdee(bmr)
                    
                    tdee_goal = tdee_maintenance
                    if goal_weight_lb < weight_lb:
                        tdee_goal -= 500
                    elif goal_weight_lb > weight_lb:
                        tdee_goal += 500
                    
                    safety_floor = 1500 if sex == 'Male' else 1200
                    if goal_weight_lb < weight_lb and tdee_goal < safety_floor:
                        tdee_goal = safety_floor
                    
                    surplus = current_total_cals - tdee_goal
                    
                    self.sidebar.highlight_recommendations(surplus)
                    
                except Exception as e:
                    print(f"Error in highlight logic: {e}")

        self.highlight_tracked_dates()

    def show_main_tracker(self):
        self.master.state('zoomed')
        self.selected_date = date.today()

        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.title(f"Calorie Counter - Logged in as: {self.current_username}")
        self.master.minsize(1000, 1000) 
        
        self.master.grid_columnconfigure(0, weight=3) 
        self.master.grid_columnconfigure(1, weight=1) 
        self.master.grid_rowconfigure(0, weight=1)
        
        main_content_frame = ctk.CTkFrame(self.master, fg_color="transparent")
        main_content_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_rowconfigure(2, weight=1)

        header_frame = ctk.CTkFrame(main_content_frame, fg_color=("gray90", "gray20"))
        header_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame, 
            text=f"User: {self.current_username} | ID: {self.current_user_id}", 
            fg_color="transparent", 
            text_color=("gray30", "gray70"),
            font=('Arial', 9, 'italic')
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ctk.CTkButton(
            header_frame, 
            text="Logout", 
            command=self.logout, 
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="white", 
            font=('Arial', 9, 'bold'),
            width=80
        ).grid(row=0, column=1, sticky="e", padx=5, pady=5)
        top_horizontal_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
        top_horizontal_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        top_horizontal_frame.grid_columnconfigure(0, weight=1) 
        top_horizontal_frame.grid_columnconfigure(1, weight=1) 
        self.profile_display = ProfileDisplayFrame(top_horizontal_frame, username=self.current_username) 
        self.profile_display.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        
        self.input_frame = InputFrame(top_horizontal_frame, self)
        self.input_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        self.input_frame.update_date_picker(self.selected_date)
        display_frame = ctk.CTkFrame(
            main_content_frame, 
            corner_radius=10, 
            fg_color="transparent", 
            border_width=0          
        )
        display_frame.grid(row=2, column=0, padx=0, pady=10, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(0, weight=2) 
        display_frame.grid_rowconfigure(1, weight=1) 

        self.entries_display = EntriesDisplay(display_frame)
        self.entries_display.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.weight_graph = WeightGraph(display_frame)
        self.weight_graph.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.sidebar = SidebarFrame(self.master)
        self.sidebar.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        self.update_all_displays()