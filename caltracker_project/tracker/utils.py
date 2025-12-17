# tracker/utils.py

def calculate_tdee(profile):
    """Calculates Total Daily Energy Expenditure (TDEE) using the Mifflin-St Jeor equation."""
    
    if not all([profile.age, profile.height, profile.current_weight, profile.sex, profile.activity_level]):
        # Return a safe default if the profile is incomplete
        return 2000 
    
    # 1. Calculate Basal Metabolic Rate (BMR)
    weight_kg = profile.current_weight * 0.453592 # lbs to kg
    height_cm = profile.height * 2.54         # inches to cm

    if profile.sex == 'Male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * profile.age) + 5
    else: # Female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * profile.age) - 161
        
    # 2. Apply Activity Factor to get TDEE
    factors = {
        'Sedentary': 1.2,
        'Moderate': 1.55,
        'Active': 1.9,
    }
    
    activity_factor = factors.get(profile.activity_level, 1.2)
    
    tdee = bmr * activity_factor
    
    # 3. Apply Goal Adjustment (1 lb per week is 500 cal adjustment)
    if profile.goal_weight and profile.current_weight:
        weight_diff = profile.current_weight - profile.goal_weight
        
        if weight_diff > 0: # User is trying to lose weight
            # Aim for 1 lb loss/week (500 cal deficit)
            tdee -= 500
        elif weight_diff < 0: # User is trying to gain weight
            # Aim for 1 lb gain/week (500 cal surplus)
            tdee += 500
            
    return max(int(tdee), 1200) # Ensure a minimum of 1200 calories

def get_exercise_recommendation(calories_consumed, tdee):
    """Provides recommendations if the user is over their calorie goal."""
    
    recommendations = []
    
    if calories_consumed > tdee:
        calorie_surplus = calories_consumed - tdee
        
        if calorie_surplus > 0 and calorie_surplus <= 300:
            recommendations.append(f"A 30-minute brisk walk could burn off the extra {calorie_surplus} calories.")
        elif calorie_surplus > 300:
            recommendations.append(f"The surplus of {calorie_surplus} calories is high. Consider 60 minutes of cardio or a vigorous gym session.")
        
    return recommendations

def calculate_bmi(profile):
    """Calculates BMI and returns a dictionary with value and category."""
    if not profile.current_weight or not profile.height:
        return None

    # Formula: (Weight(lbs) / Height(in)^2) * 703
    bmi_value = (profile.current_weight / (profile.height ** 2)) * 703
    bmi_value = round(bmi_value, 1)

    # Determine Category
    if bmi_value < 18.5:
        category = "Underweight"
        color = "text-info" 
    elif 18.5 <= bmi_value < 25:
        category = "Normal Weight"
        color = "text-success" 
    elif 25 <= bmi_value < 30:
        category = "Overweight"
        color = "text-warning" 
    else:
        category = "Obese"
        color = "text-danger"

    return {
        'value': bmi_value,
        'category': category,
        'color': color
    }