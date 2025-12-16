from django.db import models
from django.contrib.auth.models import User
from datetime import date

# 1. USER PROFILE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(help_text="Height in inches", null=True, blank=True)
    current_weight = models.FloatField(null=True, blank=True)
    goal_weight = models.FloatField(null=True, blank=True)
    sex = models.CharField(max_length=20, null=True, blank=True)
    activity_level = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. FOOD ENTRIES
class FoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.CharField(max_length=200)
    calories = models.IntegerField()
    # default=date.today allows it to be today automatically, 
    # but lets you override it if you are logging for yesterday.
    entry_date = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.meal} ({self.calories} kcal) - {self.entry_date}"

# 3. WEIGHT LOGS
class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField(default=date.today)
    weight_lb = models.FloatField()

    class Meta:
        # This acts like your SQL: UNIQUE(user_id, log_date)
        unique_together = ('user', 'log_date')
        ordering = ['-log_date'] # Default to showing newest first

    def __str__(self):
        return f"{self.user.username} - {self.weight_lb} lbs on {self.log_date}"

# 4. EXTENDED FOOD ENTRY WITH MACROS    
class FoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.CharField(max_length=100)
    calories = models.IntegerField()
    
    # --- NEW MACRO FIELDS ---
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    # ------------------------
    
    entry_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal} ({self.calories} kcal)"
    
class FoodItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    calories = models.IntegerField()
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)

    def __str__(self):
        return self.name