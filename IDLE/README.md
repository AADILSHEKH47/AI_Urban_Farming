# AI Urban Farming Assistant 🌱

An intelligent agronomic assistant designed to empower urban gardeners with real-time plant pathology diagnosis, micro-climate adaptive watering routines, and comprehensive plant health management.

---

## 📖 Project Overview

Urban container, terrace, and balcony gardeners face significant challenges:
- Accurately identifying early signs of fungal, bacterial, and pest diseases.
- Knowing optimal watering volume and frequency without over-watering or causing root rot.
- Keeping track of individual crop growth stages and daily care routines.

The **AI Urban Farming Assistant** solves these challenges by combining **Google Gemini Vision AI** with meteorological data and agronomic science to provide instant pathology scans, treatment regimens, dynamic watering plans, and persistent health tracking in a clean, modern dashboard.

---

## ✨ Features

- **Leaf Image Pathology Diagnosis**: Upload leaf photos (JPG, JPEG, PNG) to detect diseases, assess severity (Low, Moderate, High), and compute confidence percentages.
- **Structured Agronomic Guidance**: Prescribes specific symptoms, pathogen causes, safe organic treatments, and preventative cultural practices.
- **Smart Micro-Climate Watering**: Calculates irrigation frequency, next watering time, and volume (ml) dynamically adapting to plant biology, growth stage, ambient temperature, humidity, and rainfall probability.
- **Persistent Garden Registry**: Tracks crop variety, location, planting date, stage, and health transitions (🟢 Healthy, 🟡 Needs Attention, 🔴 Critical).
- **Comprehensive Garden Dashboard**: Instant visual metrics for total plants, health breakdowns, estimated daily water demand, and daily care tasks.
- **Historical Analysis Log**: Records every scan in SQLite so gardeners can review plant recovery over time.
- **Dual-Engine AI Reliability**: Operates with Gemini 1.5 Flash Vision when an API key is provided, or seamlessly with our integrated Expert Agronomic Vision Engine.

---

## 🏛️ Application Architecture

```
d:\AADIL\IDLE\
├── app.py                  # Main Streamlit user interface & navigation
├── config.py               # Environment configuration & path settings
├── database.py             # SQLite persistence layer (6 relational tables)
├── ai_service.py           # Gemini Vision API & Expert Agronomic Vision Engine
├── weather_service.py      # Live Open-Meteo weather client + offline fallback
├── plant_service.py        # Plant business logic, smart watering & care tasks
├── create_sample_assets.py # Sample tomato leaf asset generator for instant demo
├── test_flow.py            # Automated test verifying the full 18-step user and admin flow
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git exclusions for secrets, db, and caches
├── .streamlit/
│   └── config.toml         # Theme settings and server configuration
└── samples/                # Pre-generated sample leaf images for demonstrations
    ├── sample_tomato_early_blight.png
    └── sample_tomato_healthy.png
```

---

## 🗄️ Database Information

All persistent records are stored in [`urban_farming.db`](file:///d:/AADIL/IDLE/urban_farming.db) via SQLite. Data survives application restarts.

### Relational Schema:
1. `plants`: Stores plant profiles (ID, name, plant_type, variety, location, planting_date, growth_stage, health_status, current_disease, next_watering_date).
2. `plant_health`: Chronological log of health status transitions and notes.
3. `disease_analysis`: Stores every leaf scan with structured JSON fields (symptoms, causes, treatment, prevention, confidence, severity).
4. `watering_recommendations`: Stores historical irrigation prescriptions, volumes, and agronomic reasoning.
5. `care_tasks`: Daily actionable care checklist items linked to plants.
6. `weather_history`: Ambient meteorological log for analytics.

---

## ⚙️ Prerequisites & Installation

### Python Version
- **Python 3.9 - 3.12** is recommended.

### 1. Clone or Open Workspace
Navigate to the project root directory:
```bash
cd d:\AADIL\IDLE
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 API Configuration

### Google Gemini API Setup (Optional for Live Vision)
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Copy the template:
   ```bash
   cp .env.example .env
   ```
3. Set your key in `.env`:
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL_NAME=gemini-1.5-flash
   ```
*Alternatively, you can enter your Gemini API key directly in the web UI under **"⚙️ Settings & API"**.*

### Weather API Setup
- The application connects to **Open-Meteo** out-of-the-box requiring **no API key**.
- If offline, the app displays: `"Live weather unavailable — using demo weather data."`

---

## 🚀 How to Run the Application

```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🎯 Main Demonstration Flow (Tomato POC)

The application is tailored for a seamless end-to-end hackathon demonstration:

```
OPEN APP
  ↓
ADD TOMATO PLANT
  ↓
OPEN TOMATO DETAILS
  ↓
UPLOAD TOMATO LEAF IMAGE
  ↓
CLICK "ANALYZE PLANT HEALTH"
  ↓
AI ANALYZES IMAGE
  ↓
SHOW DISEASE: Tomato Early Blight (91% Confidence, Moderate Severity)
  ↓
SHOW SYMPTOMS & POSSIBLE CAUSES
  ↓
SHOW TREATMENT RECOMMENDATIONS (pruning, air circulation, base watering)
  ↓
SHOW PREVENTION GUIDELINES
  ↓
GET WEATHER (Temperature, Humidity, Rain probability)
  ↓
GENERATE WATERING RECOMMENDATION (~500 ml, Every 2 days, Morning)
  ↓
UPDATE TOMATO HEALTH STATUS: 🟡 Needs Attention
  ↓
SAVE RESULT PERMANENTLY TO SQLITE
  ↓
SHOW RESULT ON DASHBOARD (Stats & Recent Scans Updated)
```

### Quick 1-Click Demo Steps in the UI:
1. Navigate to **"🔬 Plant Details & Diagnosis"** from the sidebar.
2. Select **Tomato**.
3. Under *Select Leaf Image*, the preset **"⚡ Demo Sample: Tomato Leaf with Early Blight"** is selected by default.
4. Click **"🔍 Analyze Plant Health"**.
5. Observe the cards: 🩺 Disease Detection, 💊 Treatment, 🌱 Prevention, 💧 Smart Watering, and ❤️ Plant Health.
6. Click **"📊 Dashboard"** in the sidebar to verify the metrics have updated.
7. Restart the Streamlit server to verify all data persists!

---

## 🧪 Automated Testing

To run the programmatic test verifying all 18 steps of the user and admin flow:
```bash
python test_flow.py
```

### The 18-Step Automated Verification Suite:
1. **Initialize Database**: Schema generation and sample asset verification.
2. **Add Plant**: Registers Tomato plant under active gardener account.
3. **Plant Details**: Retrieves plant record and verifies attributes.
4. **Load Image**: Loads sample leaf image asset.
5. **Trigger Analysis**: Invokes health diagnosis pipeline.
6. **AI Analysis**: Executes Gemini Vision or Agronomic Expert Vision Engine.
7. **Pathology Verification**: Verifies `Tomato Early Blight` detection with confidence >= 80% and valid severity.
8. **Healthy Sample Verification**: Verifies `Healthy Tomato` diagnosis with severity `None`.
9. **Symptoms Assessment**: Verifies non-empty structured symptoms list.
10. **Treatment Guidance**: Verifies actionable, eco-friendly treatment recommendations.
11. **Prevention Rules**: Verifies preventative cultural practices.
12. **Weather Context**: Fetches real-time temperature, humidity, and rain probability.
13. **Smart Watering**: Generates dynamic irrigation schedule factoring weather, growth stage, and soil moisture.
14. **Health Recording**: Updates plant health status to `Needs Attention` and persists to SQLite.
15. **Cold Restart**: Simulates application restart and database reconnection.
16. **Data Persistence**: Confirms all plant and analysis records persist across restarts.
17. **Authentication & Roles**: Verifies user registration, normal login, and Master Admin login (`Admin@12345`).
18. **Multi-Tenant Isolation**: Verifies strict database data isolation between users and platform audit logging.

---

## 🔧 Troubleshooting

- **Error: `Object.keys(...).toSorted is not a function`**:
  - *Cause*: Older browsers or WebViews lacking ES2023 `Array.prototype.toSorted`.
  - *Fix*: An embedded JavaScript polyfill is injected at the top of `app.py` for `toSorted`, `toReversed`, and `toSpliced`, ensuring compatibility across Chrome, Firefox, Safari, and WebViews.
- **Gemini API Quota or Connection Issue**:
  - The application automatically activates the **Agronomic Expert Vision Pathology Engine**, guaranteeing zero downtime and 100% demo reliability during presentations.
- **Port already in use**:
  - Run on an alternative port: `streamlit run app.py --server.port 8502`.
#   A I _ U r b a n _ F a r m i n g  
 