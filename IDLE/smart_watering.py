"""
Smart Watering Module for AI Urban Farming Assistant.
Dynamically calculates watering schedules and volume based on:
- Plant type
- Growth stage
- Current temperature and weather condition
- Location (balcony, indoor, terrace)
- Optional soil moisture reading
"""

from typing import Dict, Any

# Plant base water requirements (baseline days between watering, baseline amount in ml)
PLANT_WATER_PROFILES = {
    "tomato": {
        "base_interval_days": 2,
        "base_amount_ml": 500,
        "drought_tolerance": "moderate",
        "soil_moisture_optimum": 65
    },
    "basil": {
        "base_interval_days": 1,
        "base_amount_ml": 250,
        "drought_tolerance": "low",
        "soil_moisture_optimum": 70
    },
    "lettuce": {
        "base_interval_days": 1.5,
        "base_amount_ml": 300,
        "drought_tolerance": "low",
        "soil_moisture_optimum": 75
    },
    "spinach": {
        "base_interval_days": 2,
        "base_amount_ml": 300,
        "drought_tolerance": "moderate",
        "soil_moisture_optimum": 65
    },
    "pepper": {
        "base_interval_days": 2.5,
        "base_amount_ml": 450,
        "drought_tolerance": "high",
        "soil_moisture_optimum": 60
    },
    "chili": {
        "base_interval_days": 3,
        "base_amount_ml": 400,
        "drought_tolerance": "high",
        "soil_moisture_optimum": 55
    },
    "mint": {
        "base_interval_days": 1.5,
        "base_amount_ml": 350,
        "drought_tolerance": "low",
        "soil_moisture_optimum": 70
    },
    "coriander": {
        "base_interval_days": 2,
        "base_amount_ml": 250,
        "drought_tolerance": "moderate",
        "soil_moisture_optimum": 65
    },
    "succulent": {
        "base_interval_days": 7,
        "base_amount_ml": 150,
        "drought_tolerance": "very high",
        "soil_moisture_optimum": 30
    }
}

GROWTH_STAGE_MULTIPLIERS = {
    "seedling": {"interval_mult": 0.7, "amount_mult": 0.5, "note": "shallow roots require light, frequent hydration"},
    "vegetative": {"interval_mult": 1.0, "amount_mult": 1.0, "note": "active leaf canopy development"},
    "growing": {"interval_mult": 1.0, "amount_mult": 1.0, "note": "steady vegetative growth phase"},
    "flowering": {"interval_mult": 0.85, "amount_mult": 1.25, "note": "high transpiration demand during blossom setting"},
    "fruiting": {"interval_mult": 0.8, "amount_mult": 1.3, "note": "heavy fruit swelling demands consistent soil hydration"},
    "mature": {"interval_mult": 1.1, "amount_mult": 0.9, "note": "established root system"}
}

def calculate_watering_recommendation(
    plant_type: str,
    growth_stage: str = "Growing",
    temperature: float = 30.0,
    weather_condition: str = "Partly Sunny",
    humidity: int = 55,
    rain_possibility: int = 10,
    location: str = "Balcony",
    soil_moisture_percent: int = None,
    last_watered_date: str = None,
    soil_moisture: int = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Computes an agronomic watering recommendation explaining the exact factors.
    Supports both soil_moisture and soil_moisture_percent, and last_watered_date.
    """
    if soil_moisture_percent is None:
        if soil_moisture is not None:
            soil_moisture_percent = soil_moisture
        elif "soil_moisture" in kwargs:
            soil_moisture_percent = kwargs["soil_moisture"]
    p_key = plant_type.lower().strip()
    profile = PLANT_WATER_PROFILES.get(p_key, {
        "base_interval_days": 2,
        "base_amount_ml": 400,
        "drought_tolerance": "moderate",
        "soil_moisture_optimum": 60
    })
    
    stage_key = growth_stage.lower().strip()
    stage_info = GROWTH_STAGE_MULTIPLIERS.get(stage_key, {
        "interval_mult": 1.0, "amount_mult": 1.0, "note": "standard growth stage"
    })
    
    interval_days = profile["base_interval_days"] * stage_info["interval_mult"]
    amount_ml = profile["base_amount_ml"] * stage_info["amount_mult"]
    
    reasons = []
    
    # Growth stage factor
    reasons.append(f"At the **{growth_stage}** stage, {stage_info['note']}.")
    
    # Temperature factor
    if temperature >= 35.0:
        interval_days *= 0.75
        amount_ml *= 1.2
        reasons.append(f"Elevated temperature ({temperature}°C) increases soil evapotranspiration significantly.")
    elif temperature >= 30.0:
        interval_days *= 0.85
        amount_ml *= 1.1
        reasons.append(f"Warm weather ({temperature}°C) accelerates moisture loss from container soil.")
    elif temperature < 18.0:
        interval_days *= 1.3
        amount_ml *= 0.85
        reasons.append(f"Cooler temperature ({temperature}°C) slows water uptake; avoiding root rot is key.")
        
    # Weather & Rain factor
    if rain_possibility >= 60 and "indoor" not in location.lower():
        reasons.append(f"High rain chance ({rain_possibility}%) expected — withhold manual irrigation if container is exposed to rain.")
        interval_days += 1
    elif "rain" in weather_condition.lower() and "indoor" not in location.lower():
        reasons.append("Active rain reduces watering requirement.")
        interval_days += 1.5
    elif humidity < 40:
        amount_ml *= 1.15
        reasons.append(f"Low ambient humidity ({humidity}%) increases foliage transpiration.")
    elif humidity > 75:
        interval_days *= 1.15
        amount_ml *= 0.9
        reasons.append(f"High ambient humidity ({humidity}%) slows soil moisture loss.")
        
    # Location factor
    if "balcony" in location.lower() or "terrace" in location.lower():
        amount_ml *= 1.1
        reasons.append(f"Balcony/terrace exposure increases wind-driven surface evaporation.")
    elif "indoor" in location.lower():
        interval_days *= 1.25
        amount_ml *= 0.9
        reasons.append("Indoor conditions reduce wind drying, allowing moisture retention.")
        
    # Soil moisture adjustment if measured
    if soil_moisture_percent is not None:
        if soil_moisture_percent > 70:
            reasons.append(f"Current soil moisture is high ({soil_moisture_percent}%). Allow topsoil to dry before watering.")
            interval_days += 1
        elif soil_moisture_percent < 35:
            reasons.append(f"Current soil moisture is critically dry ({soil_moisture_percent}%). Immediate watering recommended.")
            interval_days = 0.5
            
    # Round amounts and determine next watering time
    final_amount = int(round(amount_ml / 50.0) * 50)
    final_interval_days = max(1, round(interval_days))
    
    if final_interval_days <= 1:
        frequency_str = "Daily"
    elif final_interval_days == 2:
        frequency_str = "Every 2 days"
    elif final_interval_days == 3:
        frequency_str = "Every 3 days"
    else:
        frequency_str = f"Every {final_interval_days} days"

    # Recent Watering Impact on Next Watering
    days_ago = None
    if last_watered_date:
        try:
            from datetime import datetime, date
            watered_dt = datetime.strptime(last_watered_date[:10], "%Y-%m-%d").date()
            days_ago = (date.today() - watered_dt).days
        except Exception:
            pass
            
    if days_ago is not None:
        if days_ago == 0:
            reasons.append("Watered earlier today — soil is currently hydrated.")
            if final_interval_days <= 1:
                next_watering = "Tomorrow morning"
            elif final_interval_days == 2:
                next_watering = "In 2 days (Morning)"
            else:
                next_watering = f"In {final_interval_days} days (Morning)"
        elif days_ago >= final_interval_days:
            reasons.append(f"Last watered {days_ago} days ago (due every {final_interval_days} days) — watering is due now.")
            next_watering = "Today (Immediate)"
        else:
            remaining = final_interval_days - days_ago
            if remaining <= 1:
                next_watering = "Tomorrow morning"
            else:
                next_watering = f"In {remaining} days (Morning)"
            reasons.append(f"Last watered {days_ago} days ago; next session due in {remaining} day(s).")
    else:
        if final_interval_days <= 1:
            next_watering = "Tomorrow morning"
        elif final_interval_days == 2:
            next_watering = "Tomorrow morning"
        elif final_interval_days == 3:
            next_watering = "In 2 days (Morning)"
        else:
            next_watering = f"In {final_interval_days - 1} days (Morning)"
        
    best_time = "Morning (7:00 AM - 9:00 AM)"
    why_explanation = " ".join(reasons)
    
    return {
        "plant_type": plant_type,
        "frequency": frequency_str,
        "next_watering": next_watering,
        "amount_ml": final_amount,
        "amount_display": f"Approximately {final_amount} ml",
        "best_time": best_time,
        "why": why_explanation,
        "reason": why_explanation,
        "soil_moisture_guideline": f"Keep root zone at ~{profile['soil_moisture_optimum']}% field capacity"
    }

# Consistent API alias
calculate_smart_watering = calculate_watering_recommendation

