KG_PER_LB = 0.453592
M_PER_INCH = 0.0254

class ProfileCalculator:
    """Calculates BMI and TDEE/BMR based on user profile metrics."""

    ACTIVITY_FACTORS = {
        "Sedentary (Little/No Exercise)": 1.2,
        "Light (1-3 days/wk)": 1.375,
        "Moderate (3-5 days/wk)": 1.55,
        "Very Active (6-7 days/wk)": 1.725,
    }

    def __init__(self, age, height_in, weight_lb, sex, activity_level):
        try:
            self.age = int(age)
            self.height_m = float(height_in) * M_PER_INCH
            self.weight_lb = float(weight_lb)
            self.weight_kg = self.weight_lb * KG_PER_LB
            self.sex = sex
            self.activity_level = activity_level
        except (ValueError, TypeError):
            raise ValueError("Profile data must be valid numbers.")

    def calculate_bmi(self):
        if self.height_m == 0: return 0.0
        return self.weight_kg / (self.height_m ** 2)

    def get_bmi_category(self, bmi):
        if bmi < 18.5: return "Underweight"
        if bmi < 24.9: return "Healthy Weight"
        if bmi < 29.9: return "Overweight"
        return "Obese"

    def calculate_bmr(self):
        bmr = (10 * self.weight_kg) + (6.25 * (self.height_m / M_PER_INCH * 2.54)) - (5 * self.age)
        if self.sex == 'Male':
            bmr += 5
        else:
            bmr -= 161
        return round(bmr, 0)

    def calculate_tdee(self, bmr):
        factor = self.ACTIVITY_FACTORS.get(self.activity_level, 1.2)
        return round(bmr * factor, 0)