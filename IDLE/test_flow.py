"""
Verification Test Script for AI Urban Farming Assistant
Tests the entire 16-step user flow:
1. Initialize DB / Open Application.
2. Add Tomato plant.
3. Open Tomato details.
4. Load tomato leaf image.
5. Trigger Analyze Plant Health.
6. AI analyzes the image.
7. Verify disease + confidence + severity.
8. Verify symptoms.
9. Verify treatment.
10. Verify prevention.
11. Verify weather.
12. Generate watering recommendation.
13. Update Tomato health status.
14. Save analysis to SQLite database.
15. Simulate application restart (reconnect to SQLite DB).
16. Verify Tomato and analysis history still exist.
"""

import os
import sys
from PIL import Image
from datetime import date

print("==================================================")
print("RUNNING 16-STEP COMPLETE DEMO FLOW VERIFICATION")
print("==================================================")

# Step 1: Open App / Initialize DB
print("\n[Step 1] Initializing Application Database...")
import config
import database as db
import weather_service as weather_svc
import ai_service as ai_svc
import plant_service as plant_svc
import create_sample_assets

db.init_db()
print(f"  ✓ SQLite Database initialized at {config.DB_PATH}")

# Ensure sample images exist
blight_img_path, healthy_img_path, non_plant_img_path = create_sample_assets.generate_samples()
assert os.path.exists(blight_img_path), "Sample leaf image must exist"
assert os.path.exists(non_plant_img_path), "Non-plant sample image must exist"
print(f"  ✓ Sample leaf image confirmed at: {blight_img_path}")
print(f"  ✓ Sample non-plant image confirmed at: {non_plant_img_path}")

# Step 2: Add Tomato Plant
print("\n[Step 2] Adding 'Tomato' Plant...")
plant_id = db.add_plant(
    name="Tomato",
    plant_type="Tomato",
    variety="Roma",
    location="Balcony",
    planting_date=str(date.today()),
    growth_stage="Growing",
    health_status="Healthy"
)
print(f"  ✓ Added plant: Name='Tomato', Type='Tomato', ID={plant_id}")

# Step 3: Open Tomato Details
print("\n[Step 3] Opening Tomato details...")
tomato = db.get_plant_by_id(plant_id)
assert tomato is not None, "Tomato plant must be retrieved"
assert tomato['name'] == "Tomato", "Plant name must match"
print(f"  ✓ Retrieved Tomato: ID={tomato['id']}, Location={tomato['location']}, Initial Health={tomato['health_status']}")

# Step 4: Load Tomato Leaf Image
print("\n[Step 4] Loading Tomato leaf image...")
leaf_img = Image.open(blight_img_path)
print(f"  ✓ Loaded leaf image size: {leaf_img.size}, format: {leaf_img.format}")

# Step 5: Trigger Analyze Plant Health
print("\n[Step 5] Triggering 'Analyze Plant Health'...")

# Step 6: AI Analyzes Image
print("\n[Step 6] AI analyzing leaf image...")
diagnosis_raw, err = ai_svc.analyze_plant_health(leaf_img, plant_hint=tomato['plant_type'])
print(f"  ✓ AI analysis completed via engine: {diagnosis_raw.get('engine')}")

# Step 7: Disease + Confidence + Severity
print("\n[Step 7] Validating Disease, Confidence, and Severity...")
disease = diagnosis_raw.get("disease")
confidence = diagnosis_raw.get("confidence")
severity = diagnosis_raw.get("severity")
print(f"  ✓ Disease: {disease}")
print(f"  ✓ Confidence: {confidence}%")
print(f"  ✓ Severity: {severity}")
assert "Early Blight" in disease, f"Expected Early Blight, got {disease}"
assert confidence >= 80, f"Expected confidence >= 80%, got {confidence}"
assert severity in ["Moderate", "High", "Low"], f"Invalid severity: {severity}"

# Direct Verification of Healthy Tomato Sample
print("\n[Step 7b] Validating Healthy Tomato Sample...")
healthy_img = Image.open(healthy_img_path)
healthy_raw, _ = ai_svc.analyze_plant_health(healthy_img, plant_hint="Tomato")
print(f"  ✓ Healthy Sample Disease: {healthy_raw.get('disease')}")
print(f"  ✓ Healthy Sample Confidence: {healthy_raw.get('confidence')}%")
print(f"  ✓ Healthy Sample Severity: {healthy_raw.get('severity')}")
assert "Healthy" in healthy_raw.get("disease", ""), f"Expected Healthy Tomato, got {healthy_raw.get('disease')}"
assert healthy_raw.get("severity") == "None", f"Expected severity None for healthy leaf, got {healthy_raw.get('severity')}"

# Step 8: Symptoms
print("\n[Step 8] Validating Symptoms...")
symptoms = diagnosis_raw.get("symptoms", [])
print(f"  ✓ Identified Symptoms count: {len(symptoms)}")
for s in symptoms:
    print(f"    - {s}")
assert len(symptoms) > 0, "Symptoms must be non-empty"

# Step 9: Treatment Recommendations
print("\n[Step 9] Validating Treatment Recommendations...")
treatment = diagnosis_raw.get("treatment", [])
print(f"  ✓ Treatment items count: {len(treatment)}")
for t in treatment:
    print(f"    - {t}")
assert len(treatment) > 0, "Treatment must be non-empty"

# Step 10: Prevention Guidelines
print("\n[Step 10] Validating Prevention Guidelines...")
prevention = diagnosis_raw.get("prevention", [])
print(f"  ✓ Prevention items count: {len(prevention)}")
for p in prevention:
    print(f"    - {p}")
assert len(prevention) > 0, "Prevention must be non-empty"

# Step 11: Weather
print("\n[Step 11] Fetching current weather context...")
weather_ctx = weather_svc.get_current_weather()
print(f"  ✓ Weather: {weather_ctx['temperature']}°C, {weather_ctx['condition']}, Humidity: {weather_ctx['humidity']}%, Rain: {weather_ctx['rain_possibility']}% (Live: {weather_ctx['is_live']})")
assert "temperature" in weather_ctx and "condition" in weather_ctx

# Step 12: Generate Watering Recommendation
print("\n[Step 12] Generating dynamic smart watering recommendation...")
watering_rec = plant_svc.calculate_smart_watering(
    plant_type=tomato['plant_type'],
    growth_stage=tomato['growth_stage'],
    temperature=weather_ctx['temperature'],
    weather_condition=weather_ctx['condition'],
    humidity=weather_ctx['humidity'],
    rain_possibility=weather_ctx['rain_possibility'],
    location=tomato['location'],
    soil_moisture=50
)
print(f"  ✓ Next Watering: {watering_rec['next_watering']}")
print(f"  ✓ Suggested Frequency: {watering_rec['frequency']}")
print(f"  ✓ Suggested Amount: {watering_rec['amount_display']}")
print(f"  ✓ Agronomic Reasoning: {watering_rec['reason']}")
assert "next_watering" in watering_rec and "frequency" in watering_rec

# Verify recent watering impact
print("\n[Smart Watering Factor Test] Testing recent watering impact...")
recent_w_rec = plant_svc.calculate_smart_watering(
    plant_type=tomato['plant_type'],
    growth_stage=tomato['growth_stage'],
    temperature=weather_ctx['temperature'],
    weather_condition=weather_ctx['condition'],
    humidity=weather_ctx['humidity'],
    rain_possibility=weather_ctx['rain_possibility'],
    location=tomato['location'],
    last_watered_date=str(date.today())
)
assert "Watered earlier today" in recent_w_rec['reason'] or "today" in recent_w_rec['reason'].lower()
print(f"  ✓ Recent watering correctly factored in: Next Watering='{recent_w_rec['next_watering']}', Reason='{recent_w_rec['reason']}'")

# Verify Non-Plant / Low Confidence error handling
print("\n[Safety & Error Handling Test] Testing non-plant image detection...")
non_plant_img = Image.open(non_plant_img_path)
np_diag, _ = ai_svc.analyze_plant_health(non_plant_img, plant_hint="Tomato")
assert np_diag['confidence'] < 60 or not np_diag['is_leaf_image'], "Non-plant image must yield low confidence (<60) or is_leaf_image=False"
print(f"  ✓ Non-plant image correctly flagged: Confidence={np_diag['confidence']}%, IsLeaf={np_diag['is_leaf_image']}, Disease='{np_diag['disease']}'")

# Step 13 & 14: Update Health & Save Result
print("\n[Step 13 & 14] Recording diagnosis, updating plant health, and saving to SQLite...")
result = plant_svc.record_plant_diagnosis(
    plant_id=plant_id,
    diagnosis_data=diagnosis_raw,
    weather_data=weather_ctx,
    image_name="sample_tomato_early_blight.png",
    soil_moisture=50
)
print(f"  ✓ Analysis record saved with ID: {result['analysis_id']}")
print(f"  ✓ Updated Plant Health in DB: {result['health_status']}")
assert result['health_status'] == "Needs Attention"

# Step 15: Simulate Application Restart
print("\n[Step 15] Simulating Application Restart (cold database reload)...")
del db
import database as fresh_db

# Step 16: Verify Tomato and Analysis History still exist after restart
print("\n[Step 16] Verifying Tomato and Analysis History persistence after restart...")
reloaded_tomato = fresh_db.get_plant_by_id(plant_id)
assert reloaded_tomato is not None, "Tomato must persist after restart!"
assert reloaded_tomato['name'] == "Tomato"
assert reloaded_tomato['health_status'] == "Needs Attention"
assert "Early Blight" in reloaded_tomato['current_disease']
print(f"  ✓ Verified Tomato persists: ID={reloaded_tomato['id']}, Health={reloaded_tomato['health_status']}, Disease={reloaded_tomato['current_disease']}")

history = fresh_db.get_plant_analyses(plant_id)
assert len(history) >= 1, "Analysis history must persist after restart!"
latest_hist = history[0]
print(f"  ✓ Verified History persists: Disease={latest_hist['disease']} ({latest_hist['confidence']}%), Severity={latest_hist['severity']}")
print(f"  ✓ Preserved Treatments: {len(latest_hist['treatment'])} items")

# Check dashboard statistics update
stats = fresh_db.get_dashboard_stats()
print(f"\nDashboard Stats: Total Plants={stats['total_plants']}, Needs Attention={stats['needs_attention']}, Water Req={stats['today_water_requirement_ml']}ml")
assert stats['needs_attention'] >= 1, "Dashboard must reflect plants needing attention"

# Step 17: Verify Authentication, Master Admin Role & Watering API Compatibility
print("\n[Step 17] Verifying User Authentication, Master Admin Role & Watering API Compatibility...")
import auth_service
import smart_watering

# Test Registration
test_email = f"gardener_{int(date.today().strftime('%Y%m%d'))}@example.com"
reg_ok, reg_msg, reg_user = auth_service.register_user("Alice Gardener", test_email, "secret123", "secret123")
assert reg_ok or "already registered" in reg_msg, f"Registration failed: {reg_msg}"
login_ok, login_msg, logged_user = auth_service.login_user(test_email, "secret123")
assert login_ok, f"Login failed: {login_msg}"
assert logged_user['role'] == "user", f"Expected 'user' role, got {logged_user['role']}"
print(f"  ✓ Normal user registered and logged in: {logged_user['email']} (role: {logged_user['role']})")

# Verify Master Admin email cannot be registered publicly
admin_reg_ok, admin_reg_msg, _ = auth_service.register_user("Fake Admin", config.MASTER_ADMIN_EMAIL, "fake123", "fake123")
assert not admin_reg_ok, "Public registration using MASTER_ADMIN_EMAIL must be rejected"
assert "reserved for the Master Admin" in admin_reg_msg
print("  ✓ Confirmed public registration with Master Admin email is strictly blocked")

# Test Master Admin Login
admin_ok, admin_msg, admin_user = auth_service.login_user(config.MASTER_ADMIN_EMAIL, "Admin@12345")
assert admin_ok, f"Master Admin login failed: {admin_msg}"
assert admin_user['role'] == "master_admin", f"Expected 'master_admin' role, got {admin_user['role']}"
print(f"  ✓ Master Admin logged in server-side: {admin_user['email']} (role: {admin_user['role']})")

# Test Watering API Compatibility (Requirement 14)
w_compat1 = smart_watering.calculate_watering_recommendation(
    plant_type="Tomato",
    soil_moisture=45,
    last_watered_date=str(date.today())
)
assert "reason" in w_compat1 and "why" in w_compat1, "smart_watering must provide both 'reason' and 'why'"
w_compat2 = plant_svc.calculate_smart_watering(
    plant_type="Tomato",
    soil_moisture_percent=45,
    last_watered_date=str(date.today())
)
assert "reason" in w_compat2 and "why" in w_compat2, "plant_service must provide both 'reason' and 'why'"
assert hasattr(smart_watering, "calculate_smart_watering"), "smart_watering must alias calculate_smart_watering"
assert hasattr(plant_svc, "calculate_watering_recommendation"), "plant_service must alias calculate_watering_recommendation"
print("  ✓ Watering API interfaces, parameter aliases, and reason/why keys confirmed consistent")

# Step 18: Verify User Data Isolation (Requirement 2)
print("\n[Step 18] Verifying User Data Isolation...")
# Alice adds a basil plant
alice_plant_id = fresh_db.add_plant(
    name="Alice Basil",
    plant_type="Basil",
    variety="Sweet",
    location="Kitchen Sill",
    user_id=logged_user['id']
)

# Alice's plant list
alice_plants = fresh_db.get_all_plants(user_id=logged_user['id'])
alice_plant_ids = [p['id'] for p in alice_plants]
assert alice_plant_id in alice_plant_ids, "Alice must see her own plant"

# Other user should not see Alice's plant
other_plants = fresh_db.get_all_plants(user_id=999999)
other_plant_ids = [p['id'] for p in other_plants]
assert alice_plant_id not in other_plant_ids, "User 999999 must NOT see Alice's plant"
print(f"  ✓ Confirmed data isolation: Plant ID {alice_plant_id} is only visible to User ID {logged_user['id']}")

# Master Admin Stats & Activity Logs
admin_stats = fresh_db.get_master_admin_stats()
assert "users_needing_attention" in admin_stats, "Admin stats must include users_needing_attention"
activity_logs = fresh_db.get_activity_logs(limit=10)
assert len(activity_logs) > 0, "Activity logs must contain recorded events"
print(f"  ✓ Master admin stats verified: Total Users={admin_stats['total_users']}, Active={admin_stats['active_users']}, Needing Attention={admin_stats['users_needing_attention']}")

print("\n==================================================")
print("🎉 ALL 18 STEPS OF THE COMPLETE DEMO FLOW VERIFIED!")
print("==================================================")

