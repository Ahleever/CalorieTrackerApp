import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import FoodEntry, UserProfile, WeightLog, WaterEntry
from .services import FoodAPI, WeatherAPI

class TrackerAuthTests(TestCase):
    """Tests for Registration, Login, Logout, and Auth Errors"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard')

        # Create a test user for login tests
        self.user = User.objects.create_user(username='testuser', password='password123')

    @override_settings(AUTH_PASSWORD_VALIDATORS=[]) 
    def test_registration_success(self):
        """Test that a new user can register."""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',     
            'password2': 'newpassword123' 
        })
        
        if response.status_code == 200:
            print("\nFORM ERRORS:", response.context['form'].errors)
            print(response.context['form'].errors)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_success(self):
        """Test valid login credentials."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) 
        # Check if we are actually logged in by visiting a protected page
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_password(self):
        """Test login with wrong password."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should NOT redirect, usually returns 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your username and password didn't match.") 

    def test_logout(self):
        """Test logout functionality."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.logout_url)  # Assuming logout is a POST action
        
        # Check if we can no longer access dashboard
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302) # Redirects to login


class TrackerFeatureTests(TestCase):
    """Tests for Dashboard, Weight, Water, and Profile features"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        self.dashboard_url = reverse('dashboard')

    def test_log_weight(self):
        """Test logging weight via Dashboard POST."""
        response = self.client.post(self.dashboard_url, {
            'action': 'log_weight',
            'weight': 185.5,
            'date': timezone.now().date()
        })
        
        # Check redirect back to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Check Database
        self.assertTrue(WeightLog.objects.filter(user=self.user, weight_lb=185.5).exists())
        
        # Check Profile Updated automatically
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.current_weight, 185.5)

    def test_update_profile(self):
        """Test editing profile settings."""
        response = self.client.post(self.dashboard_url, {
            'action': 'update_profile',
            'age': 25,
            'height_ft': 5,
            'height_in': 10,
            'sex': 'Male',
            'activity_level': 'Active'
        })
        
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.age, 25)
        self.assertEqual(profile.height, 70) 
        self.assertEqual(profile.activity_level, 'Active')

    def test_water_intake_ajax(self):
        """Test the water add/remove JSON endpoint."""
        url = reverse('update_water')
        today = timezone.now().date().isoformat()
        
        # 1. Test Adding Water
        data = {'action': 'add', 'date': today}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['new_count'], 1)
        self.assertTrue(WaterEntry.objects.filter(user=self.user, glasses=1).exists())

        # 2. Test Removing Water
        data = {'action': 'remove', 'date': today}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.json()['new_count'], 0)


class APIServiceTests(TestCase):
    """Tests for FoodAPI and WeatherAPI using Mocks (No real internet calls)"""

    @patch('tracker.services.urllib.request.urlopen')
    def test_food_api_search(self, mock_urlopen):
        """Test that FoodAPI parses USDA JSON correctly."""
        
        # Mock the JSON response from USDA
        mock_response_data = {
            "foods": [
                {
                    "fdcId": 12345,
                    "description": "Mock Apple",
                    "brandOwner": "Nature",
                    "foodNutrients": [
                        {"nutrientId": 1008, "value": 95},  # Calories
                        {"nutrientId": 1003, "value": 0.5}, # Protein
                        {"nutrientId": 1004, "value": 0.3}, # Fat
                        {"nutrientId": 1005, "value": 25}   # Carbs
                    ]
                }
            ]
        }
        
        # Configure the mock to return this data
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Run the actual function
        api = FoodAPI()
        results = api.search_kcal_per_100g("apple")

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Mock Apple")
        self.assertEqual(results[0]['calories'], 95)
        self.assertEqual(results[0]['protein'], 0.5)

    @patch('tracker.services.requests.get')
    def test_weather_api(self, mock_get):
        """Test that WeatherAPI parses OpenWeatherMap JSON correctly."""
        
        # Mock the JSON response
        mock_json = {
            "name": "London",
            "main": {"temp": 72.5},
            "weather": [{"description": "clear sky", "icon": "01d"}]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_json
        mock_get.return_value = mock_response

        # Run the function
        service = WeatherAPI()
        data = service.get_current_weather(lat=51.5, lon=-0.12)

        # Verify results
        self.assertEqual(data['city'], "London")
        self.assertEqual(data['temp'], 72) # It rounds 72.5 to 72 or 73 depending on python version/rounding
        self.assertEqual(data['description'], "Clear Sky")