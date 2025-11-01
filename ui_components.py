import tkinter as tk
from tkinter import ttk
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from utils import ProfileCalculator, KG_PER_LB, M_PER_INCH

try:
    from tkcalendar import DateEntry 
except Exception:
    DateEntry = None

class ProfileDisplayFrame(tk.Frame):
    """A frame to display the user's calculated profile metrics."""
    def __init__(self, master, **kwargs):
        super().__init__(master, padx=15, pady=15, bg="#f0f0f0", **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        tk.Label(self, text="Metrics Summary", bg="#e0e0e0", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        
        self.labels = {
            "weight": self._create_metric_label(1, "Current Weight:"),
            "bmi": self._create_metric_label(2, "Current BMI:"),
            "tdee": self._create_metric_label(3, "Daily Maintenance (TDEE):"),
            "goal": self._create_metric_label(4, "Goal Calories:"),
            "range": self._create_metric_label(5, "Healthy Weight Range:")
        }

    def _create_metric_label(self, row, text):
        """Helper to create a label pair."""
        tk.Label(self, text=text, anchor='w', justify='left', bg="#f0f0f0", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=5, pady=2)
        value_label = tk.Label(self, text="---", anchor='e', justify='right', bg="#f0f0f0", fg="#333333", font=('Arial', 10, 'bold'))
        value_label.grid(row=row, column=1, sticky='e', padx=5, pady=2)
        return value_label

    def update_metrics(self, profile_data):
        if not profile_data or any(x is None for x in profile_data):
            self.labels["weight"].config(text="Profile Data Missing. Please update.", fg="red")
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
            self.labels["weight"].config(text=f"{weight_lb:.1f} Lbs (Goal: {goal_weight_lb:.1f} Lbs)", fg="#333333")
            self.labels["bmi"].config(text=f"{current_bmi:.1f} ({bmi_category})", fg=("#4CAF50" if bmi_category == "Healthy Weight" else "#FF9800"))
            self.labels["tdee"].config(text=f"{tdee_maintenance:.0f} kcal", fg="#0056b3")
            self.labels["goal"].config(text=f"{goal_display} ({goal_text_label})", fg="#DC3545")
            self.labels["range"].config(text=f"{min_weight_lb:.0f} - {max_weight_lb:.0f} lbs", fg="#333333")

        except ValueError as e:
            self.labels["weight"].config(text=f"Error in calculation: {e}", fg="red")


class InputFrame(tk.Frame):
    """A frame for all user inputs: date, meal, calories, and weight."""
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, padx=15, pady=15, bg="#e0e0e0", **kwargs)
        self.app = app_controller
        self.columnconfigure(1, weight=1)
        
        self.common_meals = [
            "Chicken and Rice", "Oatmeal", "Protein Shake", "Scrambled Eggs",
            "Tuna Salad", "Pasta with Sauce", "Apple", "Banana"
        ]

        self._create_date_picker()
        self._create_entry_fields()

    def _create_date_picker(self):
        date_frame = tk.Frame(self, bg="#e0e0e0")
        date_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        date_frame.grid_columnconfigure(0, weight=1) 
        date_frame.grid_columnconfigure(4, weight=1) 

        tk.Label(date_frame, text="Date:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=(0,8), sticky='e') 
        tk.Button(date_frame, text="◀ Prev", command=lambda: self.app.change_day(-1)).grid(row=0, column=1, sticky="w")
        
        self.date_picker = None
        self.date_label_var = None
        if DateEntry is not None:
            self.date_picker = DateEntry(date_frame, width=15, background='darkblue', foreground='white', 
                                         borderwidth=2, date_pattern="yyyy-mm-dd", font=('Arial', 12))
            self.date_picker.grid(row=0, column=2, padx=8) 
            self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.app.set_date(self.date_picker.get_date()))
        else:
            self.date_label_var = tk.StringVar()
            tk.Label(date_frame, textvariable=self.date_label_var, bg="#e0e0e0", font=('Arial', 10)).grid(row=0, column=2, padx=8) 
            
        tk.Button(date_frame, text="Next ▶", command=lambda: self.app.change_day(1)).grid(row=0, column=3, sticky="w") 

    def _create_entry_fields(self):
        tk.Label(self, text="Meal/Item:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.meal_var = tk.StringVar()
        self.meal_entry = ttk.Combobox(self, textvariable=self.meal_var, values=self.common_meals, 
                                     state="normal", width=30, font=('Arial', 10))
        self.meal_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self, text="Calories:", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.calories_entry = tk.Entry(self, width=30, font=('Arial', 10))
        self.calories_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self, text="Weight (Lbs):", bg="#e0e0e0", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.weight_entry = tk.Entry(self, width=30, font=('Arial', 10))
        self.weight_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.add_button = tk.Button(self, text="Add Entry / Log Weight", command=self._on_add, 
                                    bg="#4CAF50", fg="white", activebackground="#45a049", font=('Arial', 11, 'bold'))
        self.add_button.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

    def _on_add(self):
        """Passes the input values to the main app controller."""
        self.app.add_entry(
            self.meal_var.get().strip(),
            self.calories_entry.get().strip(),
            self.weight_entry.get().strip()
        )

    def clear_inputs(self):
        self.meal_var.set("")
        self.calories_entry.delete(0, tk.END)
        self.weight_entry.delete(0, tk.END)

    def update_date_picker(self, new_date):
        if self.date_picker:
            self.date_picker.set_date(new_date)
        if self.date_label_var:
            self.date_label_var.set(new_date.isoformat())


class EntriesDisplay(tk.Frame):
    """A frame to display daily totals and the list of entries for the day."""
    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#ffffff", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 

        self.total_label = tk.Label(self, text="Total Calories: 0 kcal", font=('Arial', 16, 'bold'), 
                                    fg="#E65100", bg="#ffffff")
        self.total_label.grid(row=0, column=0, sticky='ew', pady=(0, 5))

        self.weight_day_label = tk.Label(self, text="Weight Log (M/D): --- Lbs", font=('Arial', 12, 'bold'), 
                                          fg="#5c6bc0", bg="#ffffff")
        self.weight_day_label.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        tk.Label(self, text="--- Meal/Calorie Entries ---", fg="#555555", bg="#ffffff", font=('Arial', 10)).grid(row=2, column=0, sticky='ew', pady=(10, 5))
        
        text_scroll_frame = tk.Frame(self)
        text_scroll_frame.grid(row=3, column=0, sticky="nsew")
        text_scroll_frame.grid_rowconfigure(0, weight=1)
        text_scroll_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = tk.Scrollbar(text_scroll_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.entries_text = tk.Text(text_scroll_frame, height=12, bd=1, relief="sunken", wrap="word", 
                                    bg="#f9f9f9", font=('Consolas', 10), yscrollcommand=scrollbar.set)
        self.entries_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.entries_text.yview)
        self.entries_text.config(state=tk.DISABLED)

    def update_entries(self, entries, weight_data, selected_date):
        total = sum(entry['calories'] for entry in entries)
        self.total_label.config(text=f"Total Calories on {selected_date.strftime('%b %d, %Y')}: {total} kcal")

        current_weight = "---"
        selected_date_iso = selected_date.isoformat()
        for log_date, weight_lb in weight_data:
            if log_date == selected_date_iso:
                current_weight = f"{weight_lb:.1f}"
                break
        self.weight_day_label.config(text=f"Weight Log ({selected_date.strftime('%m/%d')}): {current_weight} Lbs")

        self.entries_text.config(state=tk.NORMAL)
        self.entries_text.delete(1.0, tk.END)
        
        if not entries:
            self.entries_text.insert(tk.END, f"No entries tracked for {selected_date.strftime('%A')}. Add a meal above!")
        else:
            for entry in entries:
                line = f"{entry['meal']}: {entry['calories']} kcal\n"
                self.entries_text.insert(tk.END, line)
                
        self.entries_text.config(state=tk.DISABLED)


class WeightGraph(tk.Frame):
    """A frame to display the matplotlib weight graph."""
    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#ffffff", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        tk.Label(self, text="\n📈Progress (Lbs)", font=('Arial', 12, 'bold'), 
                 fg="#333333", bg="#ffffff").grid(row=0, column=0, sticky='ew', pady=(10, 5))

        self.graph_container = tk.Frame(self, bg="#f0f0f0") 
        self.graph_container.grid(row=1, column=0, sticky="nsew", padx=0)
        self.graph_container.grid_rowconfigure(0, weight=1)
        self.graph_container.grid_columnconfigure(0, weight=1)
        
        self.fig = Figure(figsize=(8, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
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
                                 xytext=(0, 5), ha='center', fontsize=7, color='#333333')

            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.set_title('Weight Progress (Lbs)', fontsize=10, fontweight='bold')
            self.ax.set_ylabel('Weight (Lbs)', fontsize=8)
            
            self.fig.autofmt_xdate(rotation=20)
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.tick_params(axis='x', labelsize=7)
            self.ax.tick_params(axis='y', labelsize=8)

        self.fig.tight_layout(pad=0.5)
        self.canvas.draw()


class SidebarFrame(tk.Frame):
    """The sidebar for exercise recommendations and calorie history."""
    def __init__(self, master, **kwargs):
        super().__init__(master, padx=10, pady=10, bg="#eaf3ff", relief=tk.RIDGE, bd=2, **kwargs)
        self.grid_columnconfigure(0, weight=1) 
        self._create_exercise_panel()
        self._create_history_panel()
        self.grid_rowconfigure(self.history_row_index, weight=1)

    def _create_exercise_panel(self):
        tk.Label(self, text="🔥 Daily Exercise Goal 🔥", 
                  font=('Arial', 12, 'bold'), fg="#333333", bg="#eaf3ff").grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        recommendations = [
            ("Walk 30 min", "150 kcal"), ("1 hour Strength Training", "300 kcal"),
            ("20 min HIIT", "250 kcal"), ("Yoga or Stretching", "80 kcal"),
            ("Running 5k", "400 kcal"), ("Cycling (Moderate)", "350 kcal")
        ]
        
        for i, (name, calories) in enumerate(recommendations):
            item_frame = tk.Frame(self, bg="#ffffff", padx=10, pady=8, relief=tk.FLAT)
            item_frame.grid(row=i+1, column=0, sticky='ew', pady=2)
            tk.Label(item_frame, text=name, font=('Arial', 10, 'bold'), bg="#ffffff", fg="#0056b3").pack(anchor='w')
            tk.Label(item_frame, text=f"Burn Est.: {calories}", font=('Arial', 9), bg="#ffffff", fg="#666666").pack(anchor='w')
        
        tk.Label(self, text="\nTip: Consistency is key!\nMake sure to weigh yourself\nregularly and log your\nmeals for accurate tracking.", 
                  font=('Arial', 10, 'italic'), fg="#555555", bg="#eaf3ff").grid(row=len(recommendations)+1, column=0, sticky='ew', pady=(10, 0))
        
        self.history_row_index = len(recommendations) + 3 

    def _create_history_panel(self):
        hist_title_row = self.history_row_index - 1
        hist_title = tk.Label(self, text="\n📅 Recent Calorie Totals",
                              font=('Arial', 12, 'bold'), fg="#333333", bg="#eaf3ff")
        hist_title.grid(row=hist_title_row, column=0, sticky='ew', pady=(16, 6))

        hist_container = tk.Frame(self, bg="#eaf3ff")
        hist_container.grid(row=self.history_row_index, column=0, sticky="nsew")
        hist_container.grid_rowconfigure(0, weight=1)
        hist_container.grid_columnconfigure(0, weight=1)

        self.history_list = tk.Listbox(hist_container) 
        self.history_list.grid(row=0, column=0, sticky="nsew")

    def refresh_history(self, daily_totals, selected_date):
        self.history_list.delete(0, tk.END)
        for row in daily_totals:
            marker = " ←" if row['date'] == selected_date.isoformat() else ""
            self.history_list.insert(tk.END, f"{row['date']}: {row['total']} kcal{marker}")