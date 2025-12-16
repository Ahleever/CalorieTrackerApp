# tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('delete/<int:entry_id>/', views.delete_food, name='delete_food'),
    path('register/', views.register, name='register'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('api/search-food/', views.search_openfoodfacts, name='search_food_api'),
    path('delete-favorite/<int:item_id>/', views.delete_favorite, name='delete_favorite'),
]