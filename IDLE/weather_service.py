"""
Weather Service for AI Urban Farming Assistant.
Fetches live micro-climate meteorological data via Open-Meteo or WeatherAPI.
If network/API is unavailable, returns demo weather clearly marked:
"Live weather unavailable — using demo weather data."
"""

import requests
from typing import Dict, Any
import config
import database as db

WMO_CODE_MAP = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
}

def get_current_weather(city: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """
    Fetches real-time weather.
    If live API is available: returns live data and logs to SQLite.
    If live API is unavailable: returns explicit demo data with exact required message.
    """
    city_name = city or config.DEFAULT_CITY
    latitude = lat if lat is not None else config.DEFAULT_LAT
    longitude = lon if lon is not None else config.DEFAULT_LON
    
    # 1. Attempt live meteorological fetch from Open-Meteo
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,weather_code"
            f"&hourly=precipitation_probability&forecast_days=1"
        )
        response = requests.get(url, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            temp = round(current.get("temperature_2m", 28.0), 1)
            humidity = int(current.get("relative_humidity_2m", 60))
            code = current.get("weather_code", 1)
            condition = WMO_CODE_MAP.get(code, "Partly Cloudy")
            
            hourly = data.get("hourly", {})
            rain_probs = hourly.get("precipitation_probability", [15])
            rain_chance = int(max(rain_probs[:12])) if rain_probs else 15
            
            # Log to DB
            try:
                db.log_weather(temp, humidity, condition, rain_chance, True)
            except Exception:
                pass
                
            return {
                "city": city_name,
                "temperature": temp,
                "condition": condition,
                "humidity": humidity,
                "rain_possibility": rain_chance,
                "is_live": True,
                "status_message": "🟢 Live Meteorological Data Connected (Open-Meteo)"
            }
    except Exception:
        pass
        
    # 2. Section 9 Fallback Requirement:
    # "Live weather unavailable — using demo weather data."
    demo_temp = 32.0
    demo_humidity = 58
    demo_condition = "Partly Sunny"
    demo_rain = 10
    
    try:
        db.log_weather(demo_temp, demo_humidity, demo_condition, demo_rain, False)
    except Exception:
        pass

    return {
        "city": city_name,
        "temperature": demo_temp,
        "condition": demo_condition,
        "humidity": demo_humidity,
        "rain_possibility": demo_rain,
        "is_live": False,
        "status_message": "⚠️ Live weather unavailable — using demo weather data."
    }
