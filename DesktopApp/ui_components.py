import random
import re
import tkinter as tk
import tkinter.ttk as ttk
from datetime import date, datetime

import customtkinter as ctk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utils import KG_PER_LB, M_PER_INCH, ProfileCalculator

try:
    from tkcalendar import DateEntry 
except Exception:
    DateEntry = None

FRAME_BG_COLOR = ("#E3F2FD", "gray20")
NEUTRAL_BG_COLOR = ("white", "gray20") 
TEXT_COLOR = ("#1565C0", "#EAEAEA")
HEADER_BG_COLOR = ("white", "#444444")
CARD_BG_COLOR = ("white", "gray25")
METRICS_BORDER_COLOR = "#3B8ED0" 
INPUT_BORDER_COLOR = "#2ECC71"    
ENTRIES_BORDER_COLOR = "#E67E22"  
GRAPH_BORDER_COLOR = "#5C6BC0"  
EXERCISE_BORDER_COLOR = "#1ABC9C" 
HISTORY_BORDER_COLOR = "#95A5A6" 
HIGHLIGHT_COLOR = "#E74C3C"       

class ProfileDisplayFrame(ctk.CTkFrame):
    def __init__(self, master, username="User", **kwargs):
        super().__init__(master, fg_color=CARD_BG_COLOR, corner_radius=15, 
                         border_width=2, border_color=METRICS_BORDER_COLOR, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text=f"{username}'s Metrics Summary", fg_color="transparent", font=('Arial', 20, 'bold')).grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=15, sticky="ew")
        
        self.labels = {
            "weight": self._create_metric_label(1, "Current Weight:"),
            "bmi": self._create_metric_label(2, "Current BMI:"),
            "tdee": self._create_metric_label(3, "Daily Maintenance (TDEE):"),
            "goal": self._create_metric_label(4, "Goal Calories:"),
            "range": self._create_metric_label(5, "Healthy Weight Range:")
        }

    def _create_metric_label(self, row, text):
        ctk.CTkLabel(self, text=text, anchor='w', justify='left', fg_color="transparent", font=('Arial', 16, 'bold')).grid(row=row, column=0, sticky='w', padx=20, pady=2)
        value_label = ctk.CTkLabel(self, text="---", anchor='e', justify='right', fg_color="transparent", text_color=TEXT_COLOR, font=('Arial', 16, 'bold'))
        value_label.grid(row=row, column=1, sticky='e', padx=20, pady=2)
        return value_label

    def update_metrics(self, profile_data):
        if not profile_data or any(x is None for x in profile_data):
            self.labels["weight"].configure(text="Profile Data Missing. Please update.", text_color="red")
            return

        age, height_in, weight_lb, goal_weight_lb, sex, activity_level = profile_data

        try:
            calc = ProfileCalculator(age, height_in, weight_lb, sex, activity_level)
            current_bmi = calc.calculate_bmi()
            bmi_category = calc.get_bmi_category(current_bmi)
            bmr = calc.calculate_bmr()
            tdee_maintenance = calc.calculate_tdee(bmr)
            
            tdee_goal = tdee_maintenance + (-500 if goal_weight_lb < weight_lb else 500 if goal_weight_lb > weight_lb else 0)
            safety_floor = 1500 if sex == 'Male' else 1200
            if goal_weight_lb < weight_lb and tdee_goal < safety_floor:
                tdee_goal = safety_floor
            
            goal_text_label = "Loss Target" if goal_weight_lb < weight_lb else "Gain Target" if goal_weight_lb > weight_lb else "Maintain Target"
            goal_display = f"{tdee_goal:.0f} kcal"
            if goal_weight_lb < weight_lb and tdee_goal == safety_floor:
                goal_display += " (Safety Floor)"
            
            height_m = float(height_in) * M_PER_INCH
            min_weight_kg = 18.5 * (height_m ** 2)
            max_weight_kg = 24.9 * (height_m ** 2)
            min_weight_lb = round(min_weight_kg / KG_PER_LB, 0)
            max_weight_lb = round(max_weight_kg / KG_PER_LB, 0)
            
            self.labels["weight"].configure(text=f"{weight_lb:.1f} Lbs (Goal: {goal_weight_lb:.1f} Lbs)")
            self.labels["bmi"].configure(text=f"{current_bmi:.1f} ({bmi_category})", text_color=("#4CAF50" if bmi_category == "Healthy Weight" else "#FF9800"))
            self.labels["tdee"].configure(text=f"{tdee_maintenance:.0f} kcal", text_color="#0056b3")
            self.labels["goal"].configure(text=f"{goal_display} ({goal_text_label})", text_color="#DC3545")
            self.labels["range"].configure(text=f"{min_weight_lb:.0f} - {max_weight_lb:.0f} lbs")

        except ValueError as e:
            self.labels["weight"].configure(text=f"Error in calculation: {e}", text_color="red")


# --- 2. InputFrame ---
class InputFrame(ctk.CTkFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, fg_color=CARD_BG_COLOR, border_width=2, border_color=INPUT_BORDER_COLOR, corner_radius=15, **kwargs)
        self.app = app_controller
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        
        self.common_meals = [
            "Chicken and Rice", "Oatmeal", "Protein Shake", "Scrambled Eggs",
            "Tuna Salad", "Pasta with Sauce", "Apple", "Banana", "Greek Yogurt", "Almonds", "Grilled Salmon"
        ]

        self._create_date_picker()
        self._create_entry_fields()

    def _create_date_picker(self):
        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(20, 8), padx=15)
        date_frame.grid_columnconfigure(0, weight=1) 
        date_frame.grid_columnconfigure(4, weight=1) 

        ctk.CTkLabel(date_frame, text="Date:", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=0, column=0, padx=(0,8), sticky='e') 
        ctk.CTkButton(date_frame, text="◀ Prev", command=lambda: self.app.change_day(-1), width=60, fg_color="gray50").grid(row=0, column=1, sticky="w")
        
        self.date_picker = None
        self.date_label_var = None
        if DateEntry is not None:
            self.date_picker = DateEntry(date_frame, width=15, background='darkblue', foreground='white', 
                                         borderwidth=2, date_pattern="yyyy-mm-dd", font=('Arial', 14))
            self.date_picker.grid(row=0, column=2, padx=8) 
            self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.app.set_date(self.date_picker.get_date()))
        else:
            self.date_label_var = ctk.StringVar()
            ctk.CTkLabel(date_frame, textvariable=self.date_label_var, fg_color="transparent", font=('Arial', 14)).grid(row=0, column=2, padx=8) 
            
        ctk.CTkButton(date_frame, text="Next ▶", command=lambda: self.app.change_day(1), width=60, fg_color="gray50").grid(row=0, column=3, sticky="w") 

    def _create_entry_fields(self):
        # Manual Entry Section
        ctk.CTkLabel(self, text="Meal/Item:", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=20)
        self.meal_var = ctk.StringVar()
        self.meal_entry = ctk.CTkComboBox(self, variable=self.meal_var, values=self.common_meals, 
                                          state="normal", width=30, font=('Arial', 14))
        self.meal_entry.grid(row=1, column=1, padx=(5, 20), pady=5, sticky="ew")

        ctk.CTkLabel(self, text="Calories:", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=1, column=2, sticky="w", pady=5, padx=5)
        self.calories_entry = ctk.CTkEntry(self, width=30, font=('Arial', 14), placeholder_text="e.g., 500")
        self.calories_entry.grid(row=1, column=3, padx=(5, 20), pady=5, sticky="ew")

        # Add Food Button
        self.add_food_btn = ctk.CTkButton(self, text="Add Food Entry", command=self._on_add_food, 
                                        fg_color="#4CAF50", hover_color="#45A049", font=('Arial', 14, 'bold'))
        self.add_food_btn.grid(row=2, column=0, columnspan=4, pady=(10, 10), padx=20, sticky="ew")

        ctk.CTkFrame(self, height=2, fg_color="gray80").grid(row=3, column=0, columnspan=4, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(self, text="Food (API):", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=4, column=0, sticky="w", pady=5, padx=20)
        self.api_food_var = ctk.StringVar()
        self.api_food_entry = ctk.CTkEntry(self, textvariable=self.api_food_var, width=30, font=('Arial', 14))
        self.api_food_entry.grid(row=4, column=1, padx=(5, 20), pady=5, sticky="ew")

        ctk.CTkLabel(self, text="Grams:", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=4, column=2, sticky="w", pady=5, padx=5)
        self.api_grams_var = ctk.StringVar(value="100")
        self.api_grams_entry = ctk.CTkEntry(self, textvariable=self.api_grams_var, width=30, font=('Arial', 14))
        self.api_grams_entry.grid(row=4, column=3, padx=(5, 20), pady=5, sticky="ew")

        self.api_search_btn = ctk.CTkButton(self, text="Find & Add from USDA", command=self._on_api_search,
                                            fg_color="#007bff", hover_color="#0056b3", font=('Arial', 14, 'bold'))
        self.api_search_btn.grid(row=5, column=0, columnspan=4, pady=(10, 10), padx=20, sticky="ew")

        ctk.CTkFrame(self, height=2, fg_color="gray80").grid(row=6, column=0, columnspan=4, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(self, text="Weight (Lbs):", fg_color="transparent", font=('Arial', 14, 'bold')).grid(row=7, column=0, sticky="w", pady=5, padx=20)
        self.weight_entry = ctk.CTkEntry(self, width=30, font=('Arial', 14), placeholder_text="e.g., 175.5")
        self.weight_entry.grid(row=7, column=1, padx=(5, 20), pady=5, sticky="ew")

        self.log_weight_btn = ctk.CTkButton(self, text="Log Weight", command=self._on_log_weight, 
                                        fg_color=INPUT_BORDER_COLOR, hover_color="#27ae60", font=('Arial', 14, 'bold'))
        self.log_weight_btn.grid(row=7, column=2, columnspan=2, pady=10, padx=(5, 20), sticky="ew")

    def _on_add_food(self):
        self.app.add_entry(
            self.meal_var.get().strip(),
            self.calories_entry.get().strip(),
            "" 
        )

    def _on_log_weight(self):
        self.app.add_entry(
            "", 
            "", 
            self.weight_entry.get().strip()
        )

    def _on_api_search(self):
        if hasattr(self.app, "find_and_add_from_api"):
            self.app.find_and_add_from_api()
        else:
            print("API integration not found in app.py")

    def clear_inputs(self):
        self.meal_var.set("")
        self.calories_entry.delete(0, ctk.END)
        self.weight_entry.delete(0, ctk.END)
        self.api_food_var.set("")
        self.api_grams_var.set("100")

    def update_date_picker(self, new_date):
        if self.date_picker:
            self.date_picker.set_date(new_date)
        if self.date_label_var:
            self.date_label_var.set(new_date.isoformat())


class FoodPickDialog(ctk.CTkToplevel):
    def __init__(self, master, results, on_pick):
        super().__init__(master)
        self.title("Pick a food")
        
        win_width = 600
        win_height = 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width/2) - (win_width/2))
        y = int((screen_height/2) - (win_height/2))
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        self.resizable(False, False)
        self.on_pick = on_pick
        
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Select the best match:", font=("Arial", 14, "bold")).pack(pady=(15, 10))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="white", 
                        foreground="black", 
                        rowheight=25, 
                        fieldbackground="white",
                        font=('Arial', 14))
        style.map('Treeview', background=[('selected', '#347083')])

        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ("desc", "kcal", "type")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("desc", text="Description")
        self.tree.heading("kcal", text="kcal / 100g")
        self.tree.heading("type", text="Data Type")
        
        self.tree.column("desc", width=350)
        self.tree.column("kcal", width=100, anchor="center")
        self.tree.column("type", width=100, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for r in results:
            self.tree.insert("", "end", values=(r["description"], int(round(r["kcal_100g"])), r["dataType"]), iid=str(r["fdcId"]))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=15)
        
        ctk.CTkButton(btns, text="Use Selected", fg_color="#4CAF50", hover_color="#45A049", command=self.choose).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Cancel", fg_color="#E74C3C", hover_color="#C0392B", command=self.destroy).pack(side="left", padx=10)

        self.tree.bind("<Double-1>", lambda e: self.choose())

    def choose(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        desc, kcal100, dtype = values
        fdc_id = int(sel[0])
        
        self.on_pick({
            "fdcId": fdc_id, 
            "description": desc, 
            "dataType": dtype, 
            "kcal_100g": float(kcal100)
        })
        self.destroy()


class EntriesDisplay(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=CARD_BG_COLOR, corner_radius=15, 
                         border_width=2, border_color=ENTRIES_BORDER_COLOR, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 

        self.total_label = ctk.CTkLabel(self, text="Total Calories: 0 kcal", font=('Arial', 16, 'bold'), 
                                        text_color="#E65100", fg_color="transparent")
        self.total_label.grid(row=0, column=0, sticky='ew', pady=(20, 5), padx=20)

        self.weight_day_label = ctk.CTkLabel(self, text="Weight Log (M/D): --- Lbs", font=('Arial', 16, 'bold'), 
                                             text_color="#5c6bc0", fg_color="transparent")
        self.weight_day_label.grid(row=1, column=0, sticky='ew', pady=(0, 15), padx=20)
        
        ctk.CTkLabel(self, text="Daily Entries", text_color="gray50", fg_color="transparent", font=('Arial', 16, 'bold')).grid(row=2, column=0, sticky='w', padx=25, pady=(0, 5))
        
        self.entries_text = ctk.CTkTextbox(
            self, 
            height=16, 
            activate_scrollbars=True, 
            wrap="word", 
            fg_color=("gray98", "gray20"), 
            border_width=1,
            border_color="gray80",
            font=('Consolas', 11),
            corner_radius=10 
        )
        self.entries_text.grid(row=3, column=0, sticky='nsew', padx=25, pady=(0, 25))
        self.entries_text.configure(state="disabled")

    def update_entries(self, entries, weight_data, selected_date):
        total = sum(entry['calories'] for entry in entries)
        self.total_label.configure(text=f"Total Calories on {selected_date.strftime('%b %d, %Y')}: {total} kcal")

        current_weight = "---"
        selected_date_iso = selected_date.isoformat()
        for log_date, weight_lb in weight_data:
            if log_date == selected_date_iso:
                current_weight = f"{weight_lb:.1f}"
                break
        self.weight_day_label.configure(text=f"Weight Log ({selected_date.strftime('%m/%d')}): {current_weight} Lbs")

        self.entries_text.configure(state="normal")
        self.entries_text.delete("1.0", "end")
        
        if not entries:
            self.entries_text.insert("end", f"No entries tracked for {selected_date.strftime('%A')}. Add a meal above!")
        else:
            for entry in entries:
                line = f"{entry['meal']}: {entry['calories']} kcal\n"
                self.entries_text.insert("end", line)
                
        self.entries_text.configure(state="disabled")

class WeightGraph(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=CARD_BG_COLOR, corner_radius=15, 
                         border_width=2, border_color=GRAPH_BORDER_COLOR, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        ctk.CTkLabel(self, text="\n📈Progress (Lbs)", font=('Arial', 12, 'bold'), 
                     text_color=TEXT_COLOR, fg_color="transparent").grid(row=0, column=0, sticky='ew', pady=(15, 5), padx=15)

        self.graph_container = ctk.CTkFrame(self, fg_color="transparent") 
        self.graph_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.graph_container.grid_rowconfigure(0, weight=1)
        self.graph_container.grid_columnconfigure(0, weight=1)
        
        self.fig = Figure(figsize=(8, 3), dpi=100)
        
        bg_color = CARD_BG_COLOR[0] if ctk.get_appearance_mode() == "Light" else CARD_BG_COLOR[1]
        self.fig.patch.set_facecolor(bg_color)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(bg_color)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

    def plot(self, data):
        self.ax.clear()
        
        if not data:
            self.ax.text(0.5, 0.5, 'Log your first weight!', 
                         ha='center', va='center', fontsize=10, color='gray')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_title('Weight Progress', fontsize=10)
        else:
            date_strings = [item[0] for item in data]
            weights = [item[1] for item in data]
            sorted_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in date_strings]

            self.ax.plot(sorted_dates, weights, marker='o', linestyle='-', 
                          color='#5c6bc0', linewidth=2, markersize=5)
            
            for d, w in zip(sorted_dates, weights):
                self.ax.annotate(f'{w:.1f}', (d, w), textcoords="offset points", 
                                 xytext=(0, 5), ha='center', fontsize=7, color=TEXT_COLOR[0] if ctk.get_appearance_mode() == "Light" else TEXT_COLOR[1])

            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.set_title('Weight Progress (Lbs)', fontsize=10, fontweight='bold', color=TEXT_COLOR[0] if ctk.get_appearance_mode() == "Light" else TEXT_COLOR[1])
            self.ax.set_ylabel('Weight (Lbs)', fontsize=8, color=TEXT_COLOR[0] if ctk.get_appearance_mode() == "Light" else TEXT_COLOR[1])
            
            self.fig.autofmt_xdate(rotation=20)
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.tick_params(axis='x', labelsize=7, colors=TEXT_COLOR[0] if ctk.get_appearance_mode() == "Light" else TEXT_COLOR[1])
            self.ax.tick_params(axis='y', labelsize=8, colors=TEXT_COLOR[0] if ctk.get_appearance_mode() == "Light" else TEXT_COLOR[1])

        self.fig.tight_layout(pad=0.5)
        self.canvas.draw()


class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)   
        self.exercise_cards = [] 
        self.exercise_frame_container = ctk.CTkFrame(self, fg_color="transparent")
        self.exercise_frame_container.grid(row=1, column=0, sticky="ew")
        self.exercise_frame_container.grid_columnconfigure(0, weight=1)
        self._create_exercise_panel_header()
        self._create_history_panel()      
        self.current_exercises = []

    def _create_exercise_panel_header(self):
        ctk.CTkLabel(self, text="🔥 Daily Exercise Goal 🔥", 
                     font=('Arial', 12, 'bold'), text_color=TEXT_COLOR, fg_color="transparent").grid(row=0, column=0, sticky='ew', pady=(0, 10), padx=5)

    def _create_history_panel(self):
        self.hist_title = ctk.CTkLabel(self, text="\n📅 Recent Calorie Totals",
                                  font=('Arial', 12, 'bold'), text_color=TEXT_COLOR, fg_color="transparent")

        self.history_list_frame = ctk.CTkScrollableFrame(self, fg_color=CARD_BG_COLOR, corner_radius=10, 
                                                         border_width=1, border_color=HISTORY_BORDER_COLOR)
        
        self.history_labels = [] 

    def refresh_exercises(self, selected_date):
        random.seed(selected_date.toordinal()) 
        for widget in self.exercise_frame_container.winfo_children():
            widget.destroy()
        self.exercise_cards = []
        all_exercises = [
            ("Walk 30 min", "150 kcal"), 
            ("1 hour Strength Training", "300 kcal"),
            ("20 min HIIT", "250 kcal"), 
            ("Yoga or Stretching", "80 kcal"),
            ("Running 5k", "400 kcal"), 
            ("Cycling (Moderate)", "350 kcal"),
            ("Jump Rope 15 min", "200 kcal"),
            ("Swimming 30 min", "300 kcal"),
            ("Hiking 1 hour", "400 kcal"),
            ("Pilates 45 min", "180 kcal"),
            ("Dancing 30 min", "200 kcal"),
            ("Gardening 1 hour", "250 kcal"),
            ("Zumba 1 hour", "500 kcal"),
            ("Boxing 1 hour", "600 kcal"),
            ("Rowing 30 min", "250 kcal"),
            ("Elliptical 30 min", "270 kcal"),
            ("Basketball 1 hour", "600 kcal"),
            ("Tennis 1 hour", "500 kcal"),
            ("Kickboxing 45 min", "450 kcal"),
            ("Stair Climbing 20 min", "200 kcal"),
            ("Power Walking 45 min", "220 kcal"),
            ("CrossFit 1 hour", "700 kcal"),
            ("Martial Arts 1 hour", "650 kcal"),
            ("Kayaking 1 hour", "350 kcal"),
            ("Rock Climbing 1 hour", "550 kcal"),
            ("Surfing 1 hour", "300 kcal"),
            ("Badminton 1 hour", "350 kcal")
        ]       
        todays_plan = random.sample(all_exercises, 5)
        
        for i, (name, calories) in enumerate(todays_plan):
            item_frame = ctk.CTkFrame(self.exercise_frame_container, fg_color=CARD_BG_COLOR, corner_radius=10, 
                                      border_width=1, border_color=EXERCISE_BORDER_COLOR)
            item_frame.grid(row=i, column=0, sticky='ew', padx=5, pady=5)
            
            cal_int = int(re.search(r'\d+', calories).group())
            
            title_lbl = ctk.CTkLabel(item_frame, text=name, font=('Arial', 14, 'bold'),
                text_color="#0056b3")
            title_lbl.pack(anchor='w', padx=10, pady=(6, 0))
            
            cal_lbl = ctk.CTkLabel(item_frame, text=f"Burn Est.: {calories}", font=('Arial', 9),
                text_color="gray60")
            cal_lbl.pack(anchor='w', padx=10, pady=(0, 6))
            
            self.exercise_cards.append({
                'frame': item_frame,
                'burn': cal_int,
                'title': title_lbl
            })

        all_tips = [
            "Consistency is key!\nMake sure to weigh yourself\nregularly.",
            "Drink plenty of water!\nHydration aids metabolism.",
            "Protein keeps you full.\nAim for 20-30g per meal.",
            "Sleep affects weight.\nAim for 7-9 hours a night.",
            "Fiber is your friend.\nEat more veggies and fruits.",
            "Don't drink your calories.\nStick to water or tea.",
            "Meal prep helps avoid\nunhealthy last-minute choices.",
            "Eat slowly to let your brain\nregister fullness.",
            "Use smaller plates to help\ncontrol portion sizes.",
            "Plan your meals for the week\nto avoid impulse eating.",
            "Keep healthy snacks like nuts\nor fruit handy.",
            "Limit added sugars and\nsugary beverages.",
            "Aim for variety in your diet\nto get all nutrients.",
            "Don't skip breakfast; it\nkickstarts your metabolism.",
            "Take the stairs instead of\nthe elevator when possible.",
            "Park further away to get\nextra steps in.",
            "Listen to your body's\nhunger and fullness cues."
        ]       
        todays_tip = random.choice(all_tips)       
        if hasattr(self, 'tip_label'):
            self.tip_label.destroy()

        self.tip_label = ctk.CTkLabel(self, text=f"\nTip: {todays_tip}", 
                     font=('Arial', 14, 'italic'), text_color="gray50", fg_color="transparent")
        self.tip_label.grid(row=2, column=0, sticky='ew', pady=(10, 0), padx=5)

        self.hist_title.grid(row=3, column=0, sticky='ew', pady=(16, 6), padx=5)
        self.history_list_frame.grid(row=4, column=0, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)


    def refresh_history(self, daily_totals, selected_date):
        self.refresh_exercises(selected_date)

        for label in self.history_labels:
            label.destroy()
        self.history_labels = []
        
        for i, row in enumerate(daily_totals):
            date_str = datetime.strptime(row['date'], "%Y-%m-%d").strftime('%b %d')
            marker = " ←" if row['date'] == selected_date.isoformat() else ""
            
            label = ctk.CTkLabel(
                self.history_list_frame, 
                text=f"{date_str}: {row['total']} kcal{marker}",
                font=('Arial', 14),
                anchor='w',
                padx=5,
                pady=2,
                fg_color="transparent"
            )
            label.grid(row=i, column=0, sticky='ew')
            self.history_labels.append(label)

    def highlight_recommendations(self, surplus):
        """Highlights exercises based on the calorie surplus."""
        for card in self.exercise_cards:
            card['frame'].configure(border_color=EXERCISE_BORDER_COLOR, border_width=1)
            card['title'].configure(text_color="#0056b3") 

        if surplus > 0:
            candidates = [card for card in self.exercise_cards if card['burn'] >= (surplus * 0.5)]       
            if not candidates:
                 candidates = self.exercise_cards 
            candidates.sort(key=lambda x: abs(x['burn'] - surplus))           
            if candidates:
                best_match = candidates[0]
                best_match['frame'].configure(border_color=HIGHLIGHT_COLOR, border_width=3) 
                best_match['title'].configure(text_color=HIGHLIGHT_COLOR)