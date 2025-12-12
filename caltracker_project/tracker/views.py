from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import FoodEntry, UserProfile, WeightLog
from .utils import calculate_tdee, get_exercise_recommendation, calculate_bmi

@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    
    # HANDLE POST REQUESTS 
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Add Food
        if action == 'add_food':
            meal = request.POST.get('meal_name')
            cals = request.POST.get('calories')
            if meal and cals:
                FoodEntry.objects.create(user=user, meal=meal, calories=int(cals))

        # Log Weight
        elif action == 'log_weight':
            weight = request.POST.get('weight')
            date_val = request.POST.get('date') or today
            if weight:
                WeightLog.objects.update_or_create(
                    user=user, log_date=date_val,
                    defaults={'weight_lb': weight}
                )
                # Sync with profile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.current_weight = weight
                profile.save()

        # Update Profile
        elif action == 'update_profile':
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = request.POST.get('age') or None
            profile.height = request.POST.get('height') or None
            profile.current_weight = request.POST.get('weight') or None
            profile.goal_weight = request.POST.get('goal_weight') or None
            profile.sex = request.POST.get('sex')
            profile.activity_level = request.POST.get('activity_level')
            profile.save()

        return redirect('dashboard')
    
    # Display Data
    
    # Food Data
    food_entries = FoodEntry.objects.filter(user=user).order_by('-entry_date', '-id')
    today_entries = food_entries.filter(entry_date=today)
    total_calories = sum(e.calories for e in today_entries)

    # Profile & Recommendations
    profile, created = UserProfile.objects.get_or_create(user=user)
    tdee = int(calculate_tdee(profile))
    recommendations = get_exercise_recommendation(total_calories, tdee)
    bmi_data = calculate_bmi(profile)

    if tdee > 0:
        progress_percentage = (total_calories / tdee) * 100
    else:
        progress_percentage = 0

    progress_width = min(progress_percentage, 100)
        
    # Weight Data
    weight_logs = WeightLog.objects.filter(user=user).order_by('-log_date')
    
    # Prepare Chart Data (Oldest -> Newest)
    chart_data = weight_logs.order_by('log_date')
    dates = [str(log.log_date) for log in chart_data]
    weights = [float(log.weight_lb) for log in chart_data]

    context = {
        'entries': food_entries,
        'total_calories': total_calories,
        'profile': profile,
        'tdee': tdee,
        'bmi': bmi_data,
        'recommendations': recommendations,
        'logs': weight_logs[:7], # Weekly Display
        'dates': dates,
        'weights': weights,
        'progress_percentage': progress_percentage,
        'progress_width': progress_width,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def delete_food(request, entry_id):
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect('dashboard')