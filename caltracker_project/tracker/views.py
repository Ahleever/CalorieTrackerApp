# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import FoodEntry, UserProfile

@login_required
def dashboard(request):
    # 1. CHECK IF USER IS SUBMITTING DATA
    if request.method == 'POST':
        meal_name = request.POST.get('meal_name')
        calories = request.POST.get('calories')
        
        # Save to database
        if meal_name and calories:
            FoodEntry.objects.create(
                user=request.user,
                meal=meal_name,
                calories=int(calories)
            )
            # Reload the page to clear the form and show new data
            return redirect('dashboard')

    # 2. FETCH DATA TO DISPLAY
    entries = FoodEntry.objects.filter(user=request.user).order_by('-entry_date', '-id')
    total_calories = sum(entry.calories for entry in entries)
    
    context = {
        'entries': entries,
        'total_calories': total_calories
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def delete_food(request, entry_id):
    # Fetch the specific entry, but ONLY if it belongs to the logged-in user
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        entry.delete()
        
    return redirect('dashboard')

@login_required
def profile(request):
    # Get the profile, or create a blank one if it doesn't exist yet
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.age = request.POST.get('age')
        profile.height = request.POST.get('height')
        profile.current_weight = request.POST.get('weight')
        profile.goal_weight = request.POST.get('goal_weight')
        profile.sex = request.POST.get('sex')
        profile.activity_level = request.POST.get('activity_level')
        
        profile.save()
        return redirect('dashboard')  # Redirect to dashboard after saving

    return render(request, 'tracker/profile.html', {'profile': profile})