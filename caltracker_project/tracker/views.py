import requests
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login 
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_POST
from .services import FoodAPI, WeatherAPI
from datetime import datetime, timedelta  
from .models import FoodEntry, UserProfile, WeightLog, FoodItem, WaterEntry
from .utils import calculate_tdee, get_exercise_recommendation, calculate_bmi
from .forms import SignUpForm

@login_required
def dashboard(request):
    user = request.user
    
    # 1. DETERMINE DATE TO SHOW
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)
    is_today = (current_date == timezone.now().date())
    
    # 2. HANDLE POST REQUESTS 
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Action A: Add Food
        if action == 'add_food':
            meal = request.POST.get('meal_name')
            cals = request.POST.get('calories')
            prot = request.POST.get('protein') or 0
            carb = request.POST.get('carbs') or 0
            fats = request.POST.get('fat') or 0
            save_fav = request.POST.get('save_favorite')
            if meal and cals:
                FoodEntry.objects.create(
                    user=user, 
                    meal=meal, 
                    calories=int(cals),
                    protein=float(prot),
                    carbs=float(carb),
                    fat=float(fats),
                    entry_date=current_date  
                )
            if save_fav:
                    FoodItem.objects.create(
                        user=user,
                        name=meal,
                        calories=int(cals),
                        protein=float(prot),
                        carbs=float(carb),
                        fat=float(fats)
                    )

        # Action B: Log Weight
        elif action == 'log_weight':
            weight = request.POST.get('weight')
            date_val = request.POST.get('date') or current_date
            if weight:
                WeightLog.objects.update_or_create(
                    user=user, log_date=date_val,
                    defaults={'weight_lb': weight}
                )
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.current_weight = weight
                profile.save()
                messages.success(request, f"Weight logged: {weight} lbs")

        # Action C: Update Profile
        elif action == 'update_profile':
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = request.POST.get('age') or None
            h_ft = request.POST.get('height_ft')
            h_in = request.POST.get('height_in')
            # Convert to total inches for database 
            if h_ft or h_in:
                profile.height = (int(h_ft or 0) * 12) + float(h_in or 0)
            else:
                profile.height = None
            profile.current_weight = request.POST.get('weight') or None
            profile.goal_weight = request.POST.get('goal_weight') or None
            profile.sex = request.POST.get('sex')
            profile.activity_level = request.POST.get('activity_level')
            profile.save()
            messages.success(request, "Profile settings updated successfully!")

        return redirect(f"{request.path}?date={current_date}")

    # 3. FETCH DATA FOR DISPLAY 
    
    # A. Food Data 
    food_entries = FoodEntry.objects.filter(user=user).order_by('-id')
    today_entries = food_entries.filter(entry_date=current_date) 
    total_calories = sum(e.calories for e in today_entries)
    total_protein = sum(e.protein for e in today_entries)
    total_carbs = sum(e.carbs for e in today_entries)
    total_fat = sum(e.fat for e in today_entries)

    # B. Profile & Recommendations
    profile, created = UserProfile.objects.get_or_create(user=user)
    tdee = int(calculate_tdee(profile))
    recommendations = get_exercise_recommendation(total_calories, tdee)
    bmi_data = calculate_bmi(profile)

    # Progress Bar Calculation
    if tdee > 0:
        progress_percentage = (total_calories / tdee) * 100
    else:
        progress_percentage = 0
    progress_width = min(progress_percentage, 100)

    # C. Weight Data 
    weight_logs = WeightLog.objects.filter(user=user).order_by('-log_date')
    
    chart_data = weight_logs.order_by('log_date')
    dates = [str(log.log_date) for log in chart_data]
    weights = [float(log.weight_lb) for log in chart_data]

    # D. Goal Progress Message
    progress_msg = None
    if weight_logs.exists() and profile.goal_weight:
        start_weight = weight_logs.last().weight_lb
        current = profile.current_weight
        goal = profile.goal_weight
        
        change = current - start_weight
        to_go = current - goal
        
        if change < 0:
            msg_trend = f"Down {abs(change):.1f} lbs total."
        elif change > 0:
            msg_trend = f"Up {abs(change):.1f} lbs total."
        else:
            msg_trend = "No change yet."

        if abs(to_go) < 0.5:
             progress_msg = "🎉 You hit your goal weight!"
        else:
             progress_msg = f"{msg_trend} {abs(to_go):.1f} lbs to goal."

    saved_foods = FoodItem.objects.filter(user=user).order_by('name')
    if profile.height:
        display_ft = int(profile.height // 12)
        display_in = int(profile.height % 12)
    else:
        display_ft = ''
        display_in = ''

    water_entry, created = WaterEntry.objects.get_or_create(
        user=request.user, 
        date=current_date,
        defaults={'glasses': 0}
    )

    context = {
        'entries': today_entries,       
        'total_calories': total_calories,
        'total_protein': int(total_protein),
        'total_carbs': int(total_carbs),
        'total_fat': int(total_fat),
        'profile': profile,
        'tdee': tdee,
        'bmi': bmi_data,
        'recommendations': recommendations,
        'logs': weight_logs[:5],
        'dates': dates,
        'weights': weights,
        'progress_percentage': progress_percentage,
        'progress_width': progress_width,
        'progress_msg': progress_msg,
        'current_date': current_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'is_today': is_today,
        'saved_foods': saved_foods,
        'display_ft': display_ft, 
        'display_in': display_in,
        'water_glasses': water_entry.glasses,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def edit_food(request, entry_id):
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        entry.meal = request.POST.get('meal_name')
        entry.calories = int(request.POST.get('calories'))
        entry.protein = float(request.POST.get('protein') or 0)
        entry.carbs = float(request.POST.get('carbs') or 0)
        entry.fat = float(request.POST.get('fat') or 0)
        entry.save()
        
        messages.success(request, "Meal updated successfully.")
        
    return redirect(f"{reverse('dashboard')}?date={entry.entry_date}")

@login_required
def delete_food(request, entry_id):
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)
    entry_date = entry.entry_date 
    
    if request.method == 'POST':
        entry.delete()
        
    return redirect(f"{reverse('dashboard')}?date={entry_date}")

@login_required
def delete_favorite(request, item_id):
    item = get_object_or_404(FoodItem, id=item_id, user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f"Removed '{item.name}' from favorites.")
    return redirect('dashboard')

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "🎉 Account created successfully! Please set up your profile.")
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def delete_account(request):
    user = request.user
    if request.method == 'POST':
        user.delete() 
        return redirect('login')
    return redirect('dashboard')

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard') 
            
    else:
        form = SignUpForm()
    
    return render(request, 'registration/register.html', {'form': form})



def search_food(request):
    query = request.GET.get('query', '')
    
    if query:
        api = FoodAPI() 
        results = api.search_kcal_per_100g(query)
        return JsonResponse({'products': results})
    
    return JsonResponse({'products': []})

def get_weather(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    weather_service = WeatherAPI()
    weather_data = weather_service.get_current_weather(lat, lon)
    if weather_data:
        return JsonResponse(weather_data)
    else:
        return JsonResponse({'error': 'Could not fetch weather'}, status=500)
    
@login_required
@require_POST
def update_water(request):
    try:
        data = json.loads(request.body)
        action = data.get('action')
        date_str = data.get('date')
        entry, created = WaterEntry.objects.get_or_create(
            user=request.user, 
            date=date_str
        )
        
        if action == 'add':
            entry.glasses += 1
        elif action == 'remove' and entry.glasses > 0:
            entry.glasses -= 1
            
        entry.save()
        return JsonResponse({'success': True, 'new_count': entry.glasses})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})