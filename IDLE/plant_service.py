"""
Plant Service for AI Urban Farming Assistant.
Encapsulates business logic for plant management, smart watering calculations,
health status updates, care tasks, and demo seeding.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime

import database as db
import weather_service as weather_svc
import smart_watering


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
    "mint": {
        "base_interval_days": 1.5,
        "base_amount_ml": 350,
        "drought_tolerance": "low",
        "soil_moisture_optimum": 70
    },
    "chili": {
        "base_interval_days": 3,
        "base_amount_ml": 400,
        "drought_tolerance": "high",
        "soil_moisture_optimum": 55
    },
    "pepper": {
        "base_interval_days": 2.5,
        "base_amount_ml": 450,
        "drought_tolerance": "high",
        "soil_moisture_optimum": 60
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
    "seedling": {"interval_mult": 0.7, "amount_mult": 0.5, "note": "shallow root system requires light, frequent moisture"},
    "vegetative": {"interval_mult": 1.0, "amount_mult": 1.0, "note": "active foliage expansion demands consistent hydration"},
    "growing": {"interval_mult": 1.0, "amount_mult": 1.0, "note": "steady vegetative growth phase"},
    "flowering": {"interval_mult": 0.85, "amount_mult": 1.25, "note": "high transpiration demand during blossom setting"},
    "fruiting": {"interval_mult": 0.8, "amount_mult": 1.3, "note": "swelling fruits require steady soil moisture to avoid split skins"},
    "mature": {"interval_mult": 1.1, "amount_mult": 0.9, "note": "established deep root network"}
}

def calculate_smart_watering(
    plant_type: str,
    growth_stage: str = "Growing",
    temperature: float = 30.0,
    weather_condition: str = "Partly Sunny",
    humidity: int = 55,
    rain_possibility: int = 10,
    location: str = "Balcony",
    soil_moisture: Optional[int] = None,
    last_watered_date: Optional[str] = None,
    soil_moisture_percent: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Section 8: Computes smart watering recommendations.
    Uses: Plant type, growth stage, temperature, weather condition, humidity, recent watering, soil moisture.
    Outputs: Next watering time, frequency, suggested amount, reason.
    Delegates to smart_watering module to avoid logic duplication.
    """
    if soil_moisture is None and soil_moisture_percent is not None:
        soil_moisture = soil_moisture_percent
        
    rec = smart_watering.calculate_watering_recommendation(
        plant_type=plant_type,
        growth_stage=growth_stage,
        temperature=temperature,
        weather_condition=weather_condition,
        humidity=humidity,
        rain_possibility=rain_possibility,
        location=location,
        soil_moisture_percent=soil_moisture,
        last_watered_date=last_watered_date,
        soil_moisture=soil_moisture,
        **kwargs
    )
    # Ensure both reason and why exist
    rec["reason"] = rec.get("reason") or rec.get("why", "")
    rec["why"] = rec.get("why") or rec.get("reason", "")
    return rec

# Public interface compatibility alias
calculate_watering_recommendation = calculate_smart_watering


def record_plant_diagnosis(
    plant_id: int,
    diagnosis_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    image_name: str = "leaf_image.png",
    soil_moisture: Optional[int] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main orchestration function when user clicks "Analyze Plant Health":
    1. Evaluates diagnosis severity & determines health status.
    2. Computes smart watering recommendation.
    3. Saves analysis to SQLite database with user ownership.
    4. Updates plant health status and next watering in SQLite.
    5. Creates actionable care tasks.
    """
    plant = db.get_plant_by_id(plant_id)
    if not plant:
        raise ValueError(f"Plant with ID {plant_id} does not exist.")
        
    target_user_id = user_id if user_id is not None else plant.get('user_id', 1)
    dis_name = diagnosis_data.get("disease", "Unknown")
    confidence = int(diagnosis_data.get("confidence", 85))
    severity = diagnosis_data.get("severity", "Moderate")
    symptoms = diagnosis_data.get("symptoms", [])
    causes = diagnosis_data.get("possible_causes", [])
    treatment = diagnosis_data.get("treatment", [])
    prevention = diagnosis_data.get("prevention", [])
    
    # 1. Determine Health Status (Section 10)
    if "healthy" in dis_name.lower():
        health_status = "Healthy"
    elif severity.lower() == "high":
        health_status = "Critical"
    else:
        health_status = "Needs Attention"
        
    # 2. Smart Watering (Section 8)
    watering_rec = calculate_smart_watering(
        plant_type=plant['plant_type'],
        growth_stage=plant['growth_stage'],
        temperature=weather_data['temperature'],
        weather_condition=weather_data['condition'],
        humidity=weather_data['humidity'],
        rain_possibility=weather_data['rain_possibility'],
        location=plant['location'],
        soil_moisture=soil_moisture,
        last_watered_date=plant.get('last_watered_date')
    )
    
    # 3. Persist Analysis (Section 11 & 12)
    analysis_id = db.save_disease_analysis(
        plant_id=plant_id,
        plant_name=plant['name'],
        disease=dis_name,
        confidence=confidence,
        severity=severity,
        symptoms=symptoms,
        causes=causes,
        treatment=treatment,
        prevention=prevention,
        image_path=image_name,
        user_id=target_user_id
    )
    
    # 4. Save Watering Recommendation
    db.save_watering_recommendation(
        plant_id=plant_id,
        frequency=watering_rec['frequency'],
        next_watering=watering_rec['next_watering'],
        amount_ml=watering_rec['amount_ml'],
        reason=watering_rec['reason']
    )
    
    # 5. Update Plant Health in DB
    db.update_plant_health(
        plant_id=plant_id,
        health_status=health_status,
        disease=dis_name,
        next_watering=watering_rec['next_watering']
    )
    
    # 6. Generate Actionable Care Task (Section 1: "Today's Care Tasks")
    if treatment:
        db.add_care_task(
            plant_id=plant_id,
            task_description=f"{plant['name']}: {treatment[0]}",
            task_type="Treatment",
            due_date=str(date.today())
        )
    db.add_care_task(
        plant_id=plant_id,
        task_description=f"{plant['name']}: Water {watering_rec['amount_display']} ({watering_rec['next_watering']})",
        task_type="Watering",
        due_date=str(date.today())
    )
    
    return {
        "analysis_id": analysis_id,
        "disease": dis_name,
        "confidence": confidence,
        "severity": severity,
        "health_status": health_status,
        "symptoms": symptoms,
        "causes": causes,
        "treatment": treatment,
        "prevention": prevention,
        "watering": watering_rec
    }

def seed_demo_plants(user_id: int = 1):
    """
    Section 15: Optionally include demo plants:
    Tomato, Basil, Mint, Chili.
    Clearly labeled as Demo Data.
    """
    demo_plants = [
        {"name": "Balcony Tomato (Demo)", "type": "Tomato", "variety": "Roma", "location": "Balcony", "stage": "Growing", "status": "Healthy"},
        {"name": "Kitchen Basil (Demo)", "type": "Basil", "variety": "Sweet Genovese", "location": "Kitchen Sill", "stage": "Vegetative", "status": "Healthy"},
        {"name": "Terrace Mint (Demo)", "type": "Mint", "variety": "Peppermint", "location": "Terrace", "stage": "Growing", "status": "Healthy"},
        {"name": "Pot Chili (Demo)", "type": "Chili", "variety": "Bird's Eye", "location": "Balcony", "stage": "Fruiting", "status": "Healthy"}
    ]
    for p in demo_plants:
        db.add_plant(
            name=p["name"],
            plant_type=p["type"],
            variety=p["variety"],
            location=p["location"],
            planting_date=str(date.today()),
            growth_stage=p["stage"],
            health_status=p["status"],
            user_id=user_id
        )

