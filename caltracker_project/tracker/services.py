import urllib.parse
import urllib.request
import requests
import json

class FoodAPI:
    FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
    DEFAULT_API_KEY = "Ql50Qs6lFfizUbEredHizw6FHlcr2FcBMoNlr6Zu" 

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else self.DEFAULT_API_KEY

    def _http_get_json(self, url, params, timeout=10):
        qs = urllib.parse.urlencode(params)
        full = f"{url}?{qs}"
        with urllib.request.urlopen(full, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search_kcal_per_100g(self, query, page_size=12):
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": "Foundation,SR Legacy,Branded" 
        }
        try:
            js = self._http_get_json(self.FDC_SEARCH_URL, params)
        except Exception as e:
            print(f"API Error: {e}")
            return []
            
        foods = js.get("foods", []) or []
        out = []
        for f in foods:
            item = {
                "id": f.get("fdcId"),
                "name": (f.get("description") or "Unknown").strip(),
                "brand": f.get("brandOwner") or "Generic",
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            }
            
            # USDA Nutrient IDs:
            # 1008 = Calories (kcal)
            # 1003 = Protein (g)
            # 1004 = Fat (g)
            # 1005 = Carbs (g)
            for n in f.get("foodNutrients", []) or []:
                nid = str(n.get("nutrientId"))
                val = n.get("value", 0)
                
                if nid == "1008": item["calories"] = int(val)
                elif nid == "1003": item["protein"] = float(val)
                elif nid == "1004": item["fat"] = float(val)
                elif nid == "1005": item["carbs"] = float(val)

            out.append(item)
        return out
    
class WeatherAPI:
    API_KEY = "827f7dcedaccfb16c68ec0eb18a2a5a3"
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def get_current_weather(self, lat, lon):
        if not lat or not lon:
            return None

        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.API_KEY,
            'units': 'imperial'
        }
        
        try:
            # Using requests library for cleaner syntax
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            
            if response.status_code != 200:
                print(f"Weather API Error: {response.status_code}")
                return None
                
            data = response.json()
            
            return {
                'city': data.get('name'),
                'temp': round(data['main']['temp']),
                'description': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon']
            }
        except Exception as e:
            print(f"Weather Service Error: {e}")
            return None