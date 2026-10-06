"""
AI Urban Farming Assistant 🌱
Main Streamlit Application
Comprehensive implementation satisfying PS-04 Requirements, Complete Authentication & Master Admin.
"""

import streamlit as st
import os
import json
import re
from datetime import datetime, date
from typing import Optional
from PIL import Image

import config
import database as db
import auth_service
import weather_service as weather_svc
import ai_service as ai_svc
import plant_service as plant_svc
import create_sample_assets

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Fix for "Object.keys(...).toSorted is not a function"
# Injects polyfills for Array.prototype.toSorted, toReversed, toSpliced
# into the current frame, parent window, and top window
# ---------------------------------------------------------
st.components.v1.html("""
<script>
(function() {
    function installPolyfills(win) {
        if (!win || !win.Array || !win.Array.prototype) return;
        if (!win.Array.prototype.toSorted) {
            win.Array.prototype.toSorted = function(compareFn) {
                return [...this].sort(compareFn);
            };
        }
        if (!win.Array.prototype.toReversed) {
            win.Array.prototype.toReversed = function() {
                return [...this].reverse();
            };
        }
        if (!win.Array.prototype.toSpliced) {
            win.Array.prototype.toSpliced = function(start, deleteCount, ...items) {
                const copy = [...this];
                copy.splice(start, deleteCount, ...items);
                return copy;
            };
        }
    }
    installPolyfills(window);
    try { if (window.parent) installPolyfills(window.parent); } catch(e) {}
    try { if (window.top) installPolyfills(window.top); } catch(e) {}
})();
</script>
""", height=0, width=0)

# ---------------------------------------------------------
# Custom Modern Green Urban Farming Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Page Spacing */
    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }
    
    /* Header Banner */
    .app-header {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 60%, #43a047 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(27, 94, 32, 0.15);
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    .app-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        opacity: 0.92;
        color: #e8f5e9 !important;
    }

    /* Admin Header Banner */
    .admin-header {
        background: linear-gradient(135deg, #283593 0%, #4527a0 50%, #6a1b9a 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(40, 53, 147, 0.2);
    }
    .admin-header h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    .admin-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        opacity: 0.92;
        color: #ede7f6 !important;
    }
    
    /* Stat Cards */
    .stat-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        text-align: center;
        border-top: 4px solid #2e7d32;
    }
    .stat-card.alert {
        border-top: 4px solid #f57f17;
    }
    .stat-card.critical {
        border-top: 4px solid #d32f2f;
    }
    .stat-card.info {
        border-top: 4px solid #0288d1;
    }
    .stat-card.purple {
        border-top: 4px solid #6a1b9a;
    }
    .stat-num {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1b5e20;
        margin: 0.2rem 0;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    
    /* Content Cards */
    .card-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e8f5e9;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Health Badges */
    .badge-healthy {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #a5d6a7;
    }
    .badge-attention {
        background-color: #fff9c4;
        color: #f57f17;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #fff176;
    }
    .badge-critical {
        background-color: #ffebee;
        color: #c62828;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #ef9a9a;
    }

    /* Role & Status Badges */
    .badge-admin {
        background-color: #ede7f6;
        color: #4a148c;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.75rem;
        border: 1px solid #d1c4e9;
    }
    .badge-user {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.75rem;
        border: 1px solid #c8e6c9;
    }
    .badge-active {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 2px 7px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-inactive {
        background-color: #ffebee;
        color: #c62828;
        padding: 2px 7px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* Checklist Items */
    .check-item {
        padding: 5px 0;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    /* Daily Action Box */
    .action-box {
        background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
        border: 1px solid #c8e6c9;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }

    /* Activity Log Box */
    .activity-row {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .meta-snippet {
        font-family: monospace;
        font-size: 0.8rem;
        background: #f5f5f5;
        padding: 4px 8px;
        border-radius: 4px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Ensure Sample Assets & Initialize DB
# ---------------------------------------------------------
samples_dir = os.path.join(os.path.dirname(__file__), "samples")
sample_blight_path = os.path.join(samples_dir, "sample_tomato_early_blight.png")
sample_healthy_path = os.path.join(samples_dir, "sample_tomato_healthy.png")
sample_non_plant_path = os.path.join(samples_dir, "sample_non_plant.png")
if not os.path.exists(sample_blight_path) or not os.path.exists(sample_healthy_path) or not os.path.exists(sample_non_plant_path):
    try:
        create_sample_assets.generate_samples()
    except Exception:
        pass

# Ensure SQLite DB is initialized
db.init_db()

# ---------------------------------------------------------
# Authentication State Management & OAuth Callback Processing
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "📊 Dashboard"

# Safe query parameter helper
def _get_query_param(key: str) -> Optional[str]:
    try:
        if hasattr(st, "query_params"):
            val = st.query_params.get(key)
            if isinstance(val, list):
                return val[0] if val else None
            return val
        elif hasattr(st, "experimental_get_query_params"):
            params = st.experimental_get_query_params()
            val = params.get(key)
            if isinstance(val, list):
                return val[0] if val else None
            return val
    except Exception:
        pass
    return None

def _clear_query_params():
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        elif hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params()
    except Exception:
        pass

# Process incoming OAuth callback if present
oauth_code = _get_query_param("code")
oauth_state = _get_query_param("state")
if oauth_code and not st.session_state.get("authenticated", False):
    with st.spinner("Processing OAuth callback..."):
        if oauth_state == "facebook" or (config.FACEBOOK_CLIENT_ID and not config.GOOGLE_CLIENT_ID):
            auth_ok, auth_msg, auth_user = auth_service.handle_facebook_callback(oauth_code)
        else:
            auth_ok, auth_msg, auth_user = auth_service.handle_google_callback(oauth_code)
            if not auth_ok and config.FACEBOOK_CLIENT_ID:
                auth_ok, auth_msg, auth_user = auth_service.handle_facebook_callback(oauth_code)
                
        _clear_query_params()
        if auth_ok and auth_user:
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = auth_user["id"]
            st.session_state["user_role"] = auth_user["role"]
            st.session_state["user_name"] = auth_user["name"]
            st.session_state["user_email"] = auth_user["email"]
            st.session_state["logged_in_user"] = auth_user
            st.session_state["nav_page"] = "📊 Dashboard"
            st.success(auth_msg)
            st.rerun()
        else:
            st.error(f"OAuth Authentication Failed: {auth_msg}")

# ---------------------------------------------------------
# 1. USER LOGIN / REGISTER SYSTEM (Authentication Gate)
# ---------------------------------------------------------
if not st.session_state.get("authenticated", False):
    st.markdown("""
    <div style="max-width: 540px; margin: 1.5rem auto 1rem auto; text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 0.2rem;">🌱</div>
        <h1 style="color: #1b5e20; font-size: 2.1rem; font-weight: 800; margin: 0;">
            AI Urban Farming Assistant
        </h1>
        <p style="color: #388e3c; font-size: 1rem; font-weight: 500; margin: 0.3rem 0 0 0;">
            Smart Plant Health & Urban Garden Management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_center = st.columns([2, 5, 2])[1]
    
    with col_center:
        st.markdown("""
        <div class="card-box" style="margin-top: 1rem;">
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["[ Login ]", "[ Create Account ]"])
        
        # --- TAB 1: LOGIN ---
        with tab_login:
            st.markdown("#### Welcome Back to Your Garden")
            with st.form("user_login_form"):
                login_email = st.text_input("Email", placeholder="e.g. gardener@example.com").strip()
                login_pwd = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submit = st.form_submit_button("🌱 Login", type="primary", use_container_width=True)
                
            if login_submit:
                ok, msg, user = auth_service.login_user(login_email, login_pwd)
                if ok and user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_role"] = user["role"]
                    st.session_state["user_name"] = user["name"]
                    st.session_state["user_email"] = user["email"]
                    st.session_state["logged_in_user"] = user
                    st.session_state["nav_page"] = "📊 Dashboard"
                    st.success(f"✓ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
                    
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0; color: #888; font-size: 0.8rem; font-weight: 600;">
                ─── OR CONTINUE WITH ───
            </div>
            """, unsafe_allow_html=True)
            
            c_g, c_fb = st.columns(2)
            with c_g:
                g_url = auth_service.get_google_auth_url()
                if g_url:
                    st.link_button("🔵 Continue with Google", g_url, use_container_width=True)
                else:
                    if st.button("🔵 Continue with Google", key="btn_g_oauth", use_container_width=True):
                        st.info("ℹ️ Google OAuth credentials not configured in `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`). Email/password login is active.")
            with c_fb:
                fb_url = auth_service.get_facebook_auth_url()
                if fb_url:
                    st.link_button("🔵 Continue with Facebook", fb_url, use_container_width=True)
                else:
                    if st.button("🔵 Continue with Facebook", key="btn_fb_oauth", use_container_width=True):
                        st.info("ℹ️ Facebook OAuth credentials not configured in `.env` (`FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`). Email/password login is active.")

        # --- TAB 2: REGISTER ---
        with tab_register:
            st.markdown("#### Create a New Gardener Account")
            with st.form("user_register_form"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Jane Doe")
                reg_email = st.text_input("Email", placeholder="e.g. jane@example.com")
                reg_pwd = st.text_input("Password (min 6 characters)", type="password", placeholder="Enter password")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                reg_submit = st.form_submit_button("🌱 Create Account", type="primary", use_container_width=True)
                
            if reg_submit:
                ok, msg, user = auth_service.register_user(reg_name, reg_email, reg_pwd, reg_confirm)
                if ok and user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_role"] = user["role"]
                    st.session_state["user_name"] = user["name"]
                    st.session_state["user_email"] = user["email"]
                    st.session_state["logged_in_user"] = user
                    st.session_state["nav_page"] = "📊 Dashboard"
                    st.success(f"✓ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
                    
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.stop()

# ---------------------------------------------------------
# Authenticated User & Server-side Role Resolution
# ---------------------------------------------------------
current_user_id = st.session_state.get("user_id")
if not current_user_id:
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["user_role"] = None
    st.rerun()

# 1. Load current user directly from database using user_id
db_user = db.get_user_by_id(current_user_id)
if not db_user or not db_user.get("is_active"):
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["user_role"] = None
    st.session_state["logged_in_user"] = None
    st.error("Account session is invalid or deactivated. Please log in again.")
    st.rerun()

# 2. Strict verification of database role and email against MASTER_ADMIN_EMAIL
db_role = db_user.get("role", "user")
db_email = (db_user.get("email") or "").strip().lower()

# Verification succeeds ONLY if both database role == master_admin AND email == MASTER_ADMIN_EMAIL
is_master_admin = (db_role == "master_admin" and db_email == config.MASTER_ADMIN_EMAIL.lower())

# Synchronize session state from database ground truth
st.session_state["user_role"] = "master_admin" if is_master_admin else "user"
st.session_state["user_name"] = db_user.get("name", "Gardener")
st.session_state["user_email"] = db_email
current_user_name = st.session_state["user_name"]
current_email = db_email

# ---------------------------------------------------------
# User Data Isolation: Ensure Active Plant Belongs to Logged-in User
# ---------------------------------------------------------
user_plants = db.get_all_plants(user_id=current_user_id)
if "selected_plant_id" not in st.session_state or not any(p['id'] == st.session_state["selected_plant_id"] for p in user_plants):
    st.session_state["selected_plant_id"] = user_plants[0]['id'] if user_plants else None

def navigate_to(page_name, plant_id=None):
    st.session_state["nav_page"] = page_name
    if plant_id is not None:
        st.session_state["selected_plant_id"] = plant_id

# ---------------------------------------------------------
# Sidebar Navigation (Requirements 11 & 12)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌱 AI Urban Farming Assistant")
    
    if is_master_admin:
        st.markdown("### 👑 Master Admin")
        st.caption(f"👤 {current_user_name} &bull; `{current_email}`")
        nav_options = [
            "📊 Dashboard",
            "🌱 My Plants",
            "🩺 Plant Doctor",
            "💧 Smart Watering",
            "🌤 Weather",
            "📊 Health History",
            "👑 Master Admin",
            "👥 User Management",
            "📋 User Activity",
            "🔎 Global Search History",
            "⚙️ Settings"
        ]
    else:
        st.markdown(f"### 👤 Welcome, {current_user_name}")
        st.caption(f"🌱 Urban Gardener &bull; `{current_email}`")
        nav_options = [
            "📊 Dashboard",
            "🌱 My Plants",
            "🩺 Plant Doctor",
            "💧 Smart Watering",
            "🌤 Weather",
            "📊 Health History",
            "🔎 My Search History",
            "⚙️ Settings"
        ]

    # Map previous navigation labels gracefully
    nav_alias_map = {
        "🩺 Plant Doctor & Disease Detection": "🩺 Plant Doctor",
        "🩺 Plant Doctor & 📷 Disease Detection": "🩺 Plant Doctor",
        "👑 Master Admin Dashboard": "👑 Master Admin",
        "🔎 Search History": "🔎 Global Search History",
        "⚙️ Settings & API": "⚙️ Settings"
    }
    if st.session_state["nav_page"] in nav_alias_map:
        st.session_state["nav_page"] = nav_alias_map[st.session_state["nav_page"]]
        
    current_index = nav_options.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in nav_options else 0
    selected_nav = st.radio("Navigation", nav_options, index=current_index)
    if selected_nav != st.session_state["nav_page"]:
        st.session_state["nav_page"] = selected_nav
        st.rerun()

    st.markdown("---")
    
    # Logout Button (Requirement 1)
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        auth_service.logout_user(current_user_id)
        st.session_state["authenticated"] = False
        st.session_state["user_id"] = None
        st.session_state["user_role"] = None
        st.session_state["user_name"] = None
        st.session_state["user_email"] = None
        st.session_state["logged_in_user"] = None
        st.session_state["nav_page"] = "📊 Dashboard"
        st.rerun()

    st.markdown("---")
    
    # Live Weather widget in sidebar
    weather_info = weather_svc.get_current_weather()
    st.markdown("### 🌤 Weather Context")
    st.write(f"📍 **{weather_info['city']}**")
    st.write(f"🌡 **{weather_info['temperature']}°C** | {weather_info['condition']}")
    st.write(f"💧 Humidity: **{weather_info['humidity']}%**")
    st.write(f"🌧 Rain Chance: **{weather_info['rain_possibility']}%**")
    if weather_info['is_live']:
        st.success(weather_info['status_message'])
    else:
        st.warning(weather_info['status_message'])

# ---------------------------------------------------------
# Security Guard for Master Admin Pages (Requirement 19 Test 8 & 17)
# ---------------------------------------------------------
admin_restricted_pages = [
    "👑 Master Admin",
    "👑 Master Admin Dashboard",
    "👥 User Management",
    "📋 User Activity",
    "🔎 Global Search History",
    "🔎 Search History"
]
if st.session_state["nav_page"] in admin_restricted_pages and not is_master_admin:
    st.error("⛔ Access Denied. Master Admin privileges required.")
    st.session_state["nav_page"] = "📊 Dashboard"
    st.rerun()

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def render_health_badge(status: str) -> str:
    s = (status or "Healthy").strip()
    if s == "Healthy":
        return '<span class="badge-healthy">🟢 Healthy</span>'
    elif s == "Needs Attention":
        return '<span class="badge-attention">🟡 Needs Attention</span>'
    else:
        return '<span class="badge-critical">🔴 Critical</span>'

def get_plant_emoji(plant_type: str) -> str:
    p = (plant_type or "").lower().strip()
    if "tomato" in p:
        return "🍅"
    elif "basil" in p:
        return "🌿"
    elif "mint" in p:
        return "🌱"
    elif "chili" in p or "pepper" in p:
        return "🌶️"
    elif "lettuce" in p or "spinach" in p or "coriander" in p:
        return "🥬"
    elif "succulent" in p:
        return "🌵"
    return "🌱"


# =========================================================
# 1. DASHBOARD VIEW (Isolated for current user)
# =========================================================
if st.session_state["nav_page"] == "📊 Dashboard":
    st.markdown("""
    <div class="app-header">
        <h1>🌱 AI Urban Farming Dashboard</h1>
        <p>Monitor your plants' pathology, micro-climate watering demands, and daily care tasks</p>
    </div>
    """, unsafe_allow_html=True)
    
    stats = db.get_dashboard_stats(user_id=current_user_id)
    plants = db.get_all_plants(user_id=current_user_id)
    
    # 5 Top Stat Cards (Isolated to logged-in user)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Plants</div>
            <div class="stat-num">{stats['total_plants']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Healthy Plants</div>
            <div class="stat-num" style="color: #2e7d32;">{stats['healthy_plants']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card alert">
            <div class="stat-label">Needs Attention</div>
            <div class="stat-num" style="color: #f57f17;">{stats['needs_attention']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card critical">
            <div class="stat-label">Critical Plants</div>
            <div class="stat-num" style="color: #d32f2f;">{stats['critical_plants']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="stat-card info">
            <div class="stat-label">Next Watering</div>
            <div class="stat-num" style="color: #0288d1; font-size: 1.15rem; margin-top: 0.6rem;">{stats['next_watering']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # SECTION: "What should I do for my plant today?"
    st.markdown("""
    <div class="action-box">
        <h3 style="margin-top: 0; color: #1b5e20;">🌟 What should I do for my plant today?</h3>
        <p style="margin-bottom: 0.6rem; color: #2e7d32; font-size: 0.95rem;">
            Here are your priority agronomic tasks for today based on live weather and disease status:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    act_col1, act_col2 = st.columns([6, 6])
    
    with act_col1:
        st.markdown("#### 📋 Today's Care Tasks")
        care_tasks = db.get_active_care_tasks(limit=4, user_id=current_user_id)
        if not care_tasks:
            st.success("✓ All care tasks for today are completed! Your garden is thriving.")
        else:
            for task in care_tasks:
                c_t1, c_t2 = st.columns([9, 3])
                with c_t1:
                    st.write(f"• **{task['task_type']}**: {task['task_description']}")
                with c_t2:
                    if st.button("Done ✓", key=f"done_{task['id']}"):
                        db.mark_task_completed(task['id'])
                        st.rerun()

    with act_col2:
        st.markdown("#### 💧 Priority Watering Actions")
        if not plants:
            st.info("No plants added yet. Go to '🌱 My Plants' to add your crops.")
        else:
            for p in plants[:3]:
                c_w1, c_w2 = st.columns([8, 4])
                with c_w1:
                    st.write(f"**{p['name']}** ({p['plant_type']}): Next: *{p['next_watering_date'] or 'Tomorrow'}*")
                with c_w2:
                    if st.button("Water Now 💧", key=f"dash_water_{p['id']}"):
                        db.log_watering(p['id'], amount_ml=500, notes="Watered via dashboard", user_id=current_user_id)
                        st.success(f"{p['name']} watered!")
                        st.rerun()

    st.markdown("---")

    col_left, col_right = st.columns([7, 5])
    
    with col_left:
        st.markdown("### 🌿 My Plants")
        if not plants:
            st.warning("No plants added yet. Go to '🌱 My Plants' to add your first plant.")
        else:
            for p in plants:
                with st.container():
                    st.markdown(f"""
                    <div class="card-box" style="padding: 1rem; margin-bottom: 0.8rem;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <span style="font-size: 1.15rem; font-weight: 700; color: #1b5e20;">{get_plant_emoji(p['plant_type'])} {p['name']}</span>
                                <span style="color: #666; font-size: 0.85rem; margin-left: 6px;">({p['plant_type']})</span>
                                <div style="font-size: 0.85rem; color: #555; margin-top: 4px;">
                                    📍 {p['location']} &nbsp;|&nbsp; Stage: <b>{p['growth_stage']}</b> &nbsp;|&nbsp; Disease: <b>{p['current_disease']}</b>
                                </div>
                                <div style="font-size: 0.85rem; color: #0277bd; margin-top: 3px;">
                                    💧 Next Watering: <b>{p['next_watering_date'] or 'Scheduled regularly'}</b>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                {render_health_badge(p['health_status'])}
                                <div style="font-size: 0.75rem; color: #888; margin-top: 4px;">
                                    Last Analysis: {p['last_analysis_date'] or 'Not yet analyzed'}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🔍 Diagnose / View Details for {p['name']}", key=f"dash_btn_{p['id']}"):
                        navigate_to("🩺 Plant Doctor", p['id'])
                        st.rerun()

    with col_right:
        st.markdown("### 🩺 Recent Disease Detections")
        recent = db.get_recent_analyses(limit=3, user_id=current_user_id)
        if not recent:
            st.write("No diagnostic scans performed yet for your plants.")
        else:
            for item in recent:
                badge = "badge-attention" if "healthy" not in item['disease'].lower() else "badge-healthy"
                st.markdown(f"""
                <div class="card-box" style="padding: 0.9rem; margin-bottom: 0.7rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 600; color: #2e7d32;">{item['plant_name']}</span>
                        <span class="{badge}">{item['disease']} ({item['confidence']}%)</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #555; margin-top: 4px;">
                        Severity: <b>{item['severity']}</b> | Scanned: {item['created_at'][:16]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("### 💡 Recent Recommendations")
        recent_recs = db.get_recent_watering_recommendations(limit=3, user_id=current_user_id)
        if not recent_recs:
            st.write("No irrigation recommendations recorded yet.")
        else:
            for rec in recent_recs:
                st.markdown(f"""
                <div class="card-box" style="padding: 0.85rem; margin-bottom: 0.6rem; border-left: 4px solid #0288d1;">
                    <div style="font-weight: 600; color: #0277bd;">💧 {rec['plant_name']} ({rec['plant_type']})</div>
                    <div style="font-size: 0.8rem; color: #333; margin-top: 3px;">
                        Schedule: <b>{rec['frequency']}</b> &bull; Next: <b>{rec['next_watering']}</b>
                    </div>
                    <div style="font-size: 0.75rem; color: #666; margin-top: 3px;">
                        {rec['reason'][:90]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)


# =========================================================
# 2. MY PLANTS (Isolated for current user)
# =========================================================
elif st.session_state["nav_page"] == "🌱 My Plants":
    st.markdown("""
    <div class="app-header">
        <h1>🌱 Urban Garden Plants Roster</h1>
        <p>Add, edit, delete, and inspect plant details with SQLite persistence</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_roster, tab_add = st.tabs(["📋 My Plant Roster", "➕ Add New Plant"])
    
    with tab_roster:
        plants = db.get_all_plants(user_id=current_user_id)
        if not plants:
            st.info("No plants registered in your garden yet. Switch to the '➕ Add New Plant' tab or load demo plants below.")
        else:
            cols = st.columns(3)
            for idx, p in enumerate(plants):
                col_target = cols[idx % 3]
                with col_target:
                    with st.container():
                        st.markdown(f"""
                        <div class="card-box">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 1.25rem; font-weight: 700; color: #1b5e20;">{get_plant_emoji(p['plant_type'])} {p['name']}</span>
                                {render_health_badge(p['health_status'])}
                            </div>
                            <div style="font-size: 0.85rem; color: #555; margin-top: 8px;">
                                <b>Type:</b> {p['plant_type']} | <b>Variety:</b> {p['variety'] or 'Standard'}
                            </div>
                            <div style="font-size: 0.85rem; color: #555; margin-top: 4px;">
                                <b>Location:</b> {p['location']} | <b>Stage:</b> {p['growth_stage']}
                            </div>
                            <div style="font-size: 0.85rem; color: #555; margin-top: 4px;">
                                <b>Disease:</b> {p['current_disease']}
                            </div>
                            <div style="font-size: 0.85rem; color: #0277bd; margin-top: 4px;">
                                <b>Next Watering:</b> {p['next_watering_date'] or 'Scheduled'}
                            </div>
                            <div style="font-size: 0.75rem; color: #888; margin-top: 4px;">
                                <b>Last Analysis:</b> {p['last_analysis_date'] or 'None'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander(f"✏️ Edit Details for {p['name']}"):
                            with st.form(f"roster_edit_form_{p['id']}"):
                                pe_name = st.text_input("Name", value=p['name'], key=f"pe_n_{p['id']}")
                                pe_type = st.selectbox("Type", ["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"], index=["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"].index(p['plant_type']) if p['plant_type'] in ["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"] else 0, key=f"pe_t_{p['id']}")
                                pe_var = st.text_input("Variety", value=p.get('variety', ''), key=f"pe_v_{p['id']}")
                                pe_loc = st.selectbox("Location", ["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"], index=["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"].index(p['location']) if p['location'] in ["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"] else 0, key=f"pe_l_{p['id']}")
                                pe_stage = st.selectbox("Stage", ["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"], index=["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"].index(p['growth_stage']) if p['growth_stage'] in ["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"] else 2, key=f"pe_s_{p['id']}")
                                pe_status = st.selectbox("Health", ["Healthy", "Needs Attention", "Critical"], index=["Healthy", "Needs Attention", "Critical"].index(p['health_status']) if p['health_status'] in ["Healthy", "Needs Attention", "Critical"] else 0, key=f"pe_h_{p['id']}")
                                if st.form_submit_button("Update Plant", use_container_width=True):
                                    db.update_plant(p['id'], pe_name, pe_type, pe_var, pe_loc, p.get('planting_date', ''), pe_stage, pe_status, user_id=current_user_id)
                                    st.success(f"{pe_name} updated!")
                                    st.rerun()

                        c_btn1, c_btn2 = st.columns([7, 5])
                        with c_btn1:
                            if st.button("🔍 Diagnose / Details", key=f"open_det_{p['id']}", use_container_width=True):
                                navigate_to("🩺 Plant Doctor", p['id'])
                                st.rerun()
                        with c_btn2:
                            if st.button("🗑 Delete", key=f"del_card_{p['id']}", type="secondary", use_container_width=True):
                                db.delete_plant(p['id'], user_id=current_user_id)
                                st.rerun()

    with tab_add:
        st.markdown("### Add a New Plant to Your Urban Garden")
        col_form, col_demo = st.columns([7, 5])
        
        with col_form:
            with st.form("add_plant_form"):
                f_name = st.text_input("Plant Name*", value="Tomato", help="e.g. Balcony Tomato")
                f_type = st.selectbox("Plant Type*", ["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"])
                f_variety = st.text_input("Variety (Optional)", value="Roma", help="e.g. Roma, Cherry, Genovese")
                f_loc = st.selectbox("Location*", ["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"])
                f_date = st.date_input("Planting Date", value=date.today())
                f_stage = st.selectbox("Growth Stage*", ["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"])
                f_status = st.selectbox("Initial Health Status*", ["Healthy", "Needs Attention", "Critical"])
                
                submitted = st.form_submit_button("🌱 Save Plant Permanently", type="primary", use_container_width=True)
                if submitted:
                    if not f_name.strip():
                        st.error("Please enter a valid plant name.")
                    else:
                        new_id = db.add_plant(
                            name=f_name.strip(),
                            plant_type=f_type,
                            variety=f_variety.strip(),
                            location=f_loc,
                            planting_date=str(f_date),
                            growth_stage=f_stage,
                            health_status=f_status,
                            user_id=current_user_id
                        )
                        st.success(f"Plant '{f_name}' saved to your garden successfully!")
                        navigate_to("🩺 Plant Doctor", new_id)
                        st.rerun()

        with col_demo:
            st.markdown("### ⚡ Quick Demo Seeding")
            st.write("Load pre-configured demo plants into your account for testing:")
            if st.button("🌱 Load Demo Plants (Tomato, Basil, Mint, Chili)", use_container_width=True):
                plant_svc.seed_demo_plants(user_id=current_user_id)
                st.success("Demo plants added to your garden successfully!")
                st.rerun()


# =========================================================
# 3. PLANT DOCTOR (Main Demo Flow)
# =========================================================
elif st.session_state["nav_page"] in ["🩺 Plant Doctor", "🩺 Plant Doctor & Disease Detection"]:
    st.markdown("""
    <div class="app-header">
        <h1>🩺 Plant Doctor</h1>
        <p>AI-Powered Plant Pathology, Treatment Guidelines & Micro-Climate Smart Watering</p>
    </div>
    """, unsafe_allow_html=True)
    
    plants = db.get_all_plants(user_id=current_user_id)
    if not plants:
        st.warning("No plants available in your garden yet. Please add a plant in '🌱 My Plants' to begin diagnosis.")
        st.stop()
        
    # Plant Selector
    plant_map = {f"{p['name']} ({p['plant_type']}) - ID: {p['id']}": p['id'] for p in plants}
    default_key = [k for k, v in plant_map.items() if v == st.session_state.get("selected_plant_id")]
    selected_idx = list(plant_map.keys()).index(default_key[0]) if default_key else 0
    
    selected_label = st.selectbox("Active Plant for Diagnosis:", list(plant_map.keys()), index=selected_idx)
    active_plant_id = plant_map[selected_label]
    st.session_state["selected_plant_id"] = active_plant_id
    current_plant = db.get_plant_by_id(active_plant_id, user_id=current_user_id)
    
    if not current_plant:
        st.error("Selected plant could not be accessed.")
        st.stop()
    
    # Plant Overview Card
    st.markdown(f"""
    <div class="card-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.4rem; font-weight: 700; color: #1b5e20;">{get_plant_emoji(current_plant['plant_type'])} {current_plant['name']}</span>
                <span style="font-size: 1rem; color: #555; margin-left: 8px;">({current_plant['plant_type']})</span>
            </div>
            <div>{render_health_badge(current_plant['health_status'])}</div>
        </div>
        <div style="margin-top: 8px; font-size: 0.9rem; color: #444;">
            📍 <b>Location:</b> {current_plant['location']} &nbsp;|&nbsp; 
            🏷 <b>Variety:</b> {current_plant['variety'] or 'Standard'} &nbsp;|&nbsp; 
            📈 <b>Stage:</b> {current_plant['growth_stage']} &nbsp;|&nbsp; 
            🗓 <b>Planted:</b> {current_plant['planting_date'] or 'N/A'}
        </div>
        <div style="margin-top: 4px; font-size: 0.9rem; color: #0277bd;">
            🦠 <b>Current Disease:</b> {current_plant['current_disease']} &nbsp;|&nbsp; 
            💧 <b>Next Watering:</b> {current_plant['next_watering_date'] or 'Regularly scheduled'} &nbsp;|&nbsp; 
            🔍 <b>Last Analysis:</b> {current_plant['last_analysis_date'] or 'None yet'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # LEAF IMAGE UPLOAD & PREVIEW
    st.markdown("### 📸 Upload Leaf Image for Disease Detection")
    u_col1, u_col2 = st.columns([6, 6])
    
    with u_col1:
        img_source = st.radio(
            "Select Leaf Image:",
            [
                "⚡ Demo Sample: Tomato Leaf with Early Blight",
                "⚡ Demo Sample: Healthy Tomato Leaf",
                "⚡ Demo Sample: Non-plant Image (Test Error Handling)",
                "📁 Upload Leaf Image from Computer (JPG, JPEG, PNG)"
            ],
            index=0
        )
        
        leaf_img = None
        img_filename = "sample_tomato_early_blight.png"
        
        if img_source == "⚡ Demo Sample: Tomato Leaf with Early Blight":
            if os.path.exists(sample_blight_path):
                leaf_img = Image.open(sample_blight_path)
                img_filename = "sample_tomato_early_blight.png"
        elif img_source == "⚡ Demo Sample: Healthy Tomato Leaf":
            if os.path.exists(sample_healthy_path):
                leaf_img = Image.open(sample_healthy_path)
                img_filename = "sample_tomato_healthy.png"
        elif img_source == "⚡ Demo Sample: Non-plant Image (Test Error Handling)":
            if os.path.exists(sample_non_plant_path):
                leaf_img = Image.open(sample_non_plant_path)
                img_filename = "sample_non_plant.png"
        else:
            file_upload = st.file_uploader("Choose leaf image file (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])
            if file_upload:
                try:
                    leaf_img = Image.open(file_upload)
                    if leaf_img.mode != "RGB":
                        leaf_img = leaf_img.convert("RGB")
                    img_filename = file_upload.name
                except Exception as e:
                    st.error(f"Error loading image: {e}. Please upload a valid JPG, JPEG, or PNG image.")
                    leaf_img = None
                
        soil_reading = st.slider("Soil Moisture Sensor Reading (% - optional):", min_value=10, max_value=90, value=50)

    with u_col2:
        if leaf_img is not None:
            st.image(leaf_img, caption=f"Leaf Image Preview: {img_filename}", use_container_width=True)
        else:
            st.info("No leaf image selected yet. Choose a demo sample or upload a file.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analyze Button
    analyze_btn = st.button("🔍 Analyze Plant Health", type="primary", use_container_width=True)
    
    if analyze_btn:
        if leaf_img is None:
            st.error("Please upload or select a leaf image first.")
        else:
            with st.spinner("🤖 AI analyzing leaf cellular symptoms with Gemini Vision / Expert Pathology..."):
                weather_ctx = weather_svc.get_current_weather()
                diagnosis_raw, api_note = ai_svc.analyze_plant_health(
                    image=leaf_img,
                    plant_hint=current_plant['plant_type'],
                    user_api_key=st.session_state.get("user_gemini_key")
                )
                if api_note:
                    st.info(f"ℹ️ {api_note}. Utilizing Agronomic Expert Diagnostic Engine.")
                
                conf = diagnosis_raw.get("confidence", 0)
                is_leaf = diagnosis_raw.get("is_leaf_image", True)
                dis_name = diagnosis_raw.get("disease", "")
                
                if conf < 60 or not is_leaf or "non-plant" in dis_name.lower() or "unidentifiable" in dis_name.lower():
                    st.warning("⚠️ **Unable to confidently identify the plant condition. Please upload a clearer image.**")
                    st.stop()
                    
                result = plant_svc.record_plant_diagnosis(
                    plant_id=current_plant['id'],
                    diagnosis_data=diagnosis_raw,
                    weather_data=weather_ctx,
                    image_name=img_filename,
                    soil_moisture=soil_reading,
                    user_id=current_user_id
                )
                
                st.session_state["scan_result"] = result
                st.session_state["scan_plant_id"] = current_plant['id']
                st.session_state["scan_weather"] = weather_ctx
                st.session_state["scan_engine"] = diagnosis_raw.get("engine", "AI Pathology")
                
            st.success("✅ Diagnosis Complete & Saved to Database!")
            st.rerun()

    # DISPLAY AI DIAGNOSTIC REPORT
    res = None
    w_ctx = None
    engine_used = "AI Pathology"
    
    if "scan_result" in st.session_state and st.session_state.get("scan_plant_id") == current_plant['id']:
        res = st.session_state["scan_result"]
        w_ctx = st.session_state.get("scan_weather", weather_svc.get_current_weather())
        engine_used = st.session_state.get("scan_engine", "AI Pathology")
    else:
        past_scans = db.get_plant_analyses(current_plant['id'], user_id=current_user_id)
        if past_scans:
            latest_s = past_scans[0]
            latest_w = db.get_latest_watering_recommendation(current_plant['id'])
            w_rec = {
                "next_watering": latest_w['next_watering'] if latest_w else (current_plant['next_watering_date'] or "Tomorrow morning"),
                "frequency": latest_w['frequency'] if latest_w else "Every 2 days",
                "amount_display": f"Approximately {latest_w['amount_ml']} ml" if latest_w else "Approximately 500 ml",
                "reason": latest_w['reason'] if latest_w else "Regular irrigation schedule based on plant type and weather."
            }
            res = {
                "disease": latest_s['disease'],
                "confidence": latest_s['confidence'],
                "severity": latest_s['severity'],
                "health_status": current_plant['health_status'],
                "symptoms": latest_s.get('symptoms', []),
                "causes": latest_s.get('causes', []),
                "treatment": latest_s.get('treatment', []),
                "prevention": latest_s.get('prevention', []),
                "watering": w_rec
            }
            w_ctx = weather_svc.get_current_weather()
            engine_used = "Saved Pathology Record (SQLite)"

    if res is not None:
        st.markdown("---")
        st.markdown("## 📋 Diagnostic Prescription & Care Plan")
        
        r1_c1, r1_c2, r1_c3 = st.columns(3)
        with r1_c1:
            st.markdown(f"""
            <div class="card-box">
                <div class="card-header">🩺 Disease Detection</div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #b71c1c;">{res['disease']}</div>
                <div style="margin: 6px 0; font-size: 1rem;">
                    <b>Confidence:</b> <span style="color: #2e7d32; font-weight: 700;">{res['confidence']}%</span>
                </div>
                <div><b>Severity:</b> <span style="font-weight: 600;">{res['severity']}</span></div>
                <div style="font-size: 0.75rem; color: #666; margin-top: 6px;">Engine: {engine_used}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with r1_c2:
            st.markdown(f"""
            <div class="card-box">
                <div class="card-header">❤️ Updated Plant Health</div>
                <div style="margin-top: 6px;">{render_health_badge(res['health_status'])}</div>
                <div style="font-size: 0.85rem; color: #444; margin-top: 10px;">
                    Health status recorded permanently in SQLite database.
                </div>
                <div style="font-size: 0.8rem; color: #666; margin-top: 4px;">
                    Plant: <b>{current_plant['name']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with r1_c3:
            st.markdown(f"""
            <div class="card-box">
                <div class="card-header">🌤 Micro-Climate Weather</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #0277bd;">{w_ctx['temperature']}°C | {w_ctx['condition']}</div>
                <div style="font-size: 0.85rem; margin-top: 4px;">💧 Humidity: <b>{w_ctx['humidity']}%</b></div>
                <div style="font-size: 0.85rem;">🌧 Rain Chance: <b>{w_ctx['rain_possibility']}%</b></div>
                <div style="font-size: 0.75rem; color: #666; margin-top: 4px;">{w_ctx.get('status_message', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            st.markdown("""
            <div class="card-box">
                <div class="card-header">🔍 Observed Symptoms & Pathogen Causes</div>
            """, unsafe_allow_html=True)
            st.markdown("**Visible Symptoms:**")
            for s in res.get("symptoms", []):
                st.markdown(f"- {s}")
            st.markdown("**Possible Causes:**")
            for c in res.get("causes", []):
                st.markdown(f"- {c}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("""
            <div class="card-box">
                <div class="card-header">💊 Treatment Recommendations</div>
            """, unsafe_allow_html=True)
            for t in res.get("treatment", []):
                st.markdown(f"""
                <div class="check-item">
                    <span style="color: #2e7d32; font-weight: bold;">{t}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with r2_c2:
            st.markdown("""
            <div class="card-box">
                <div class="card-header">🌱 Prevention Guidelines</div>
            """, unsafe_allow_html=True)
            for p in res.get("prevention", []):
                st.markdown(f"""
                <div class="check-item">
                    <span style="color: #1b5e20;">{p}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            w_rec = res.get("watering", {})
            st.markdown(f"""
            <div class="card-box">
                <div class="card-header">💧 Smart Watering Recommendation</div>
                <div style="font-size: 1.15rem; color: #01579b; font-weight: 700; margin-bottom: 0.4rem;">
                    Next Watering: {w_rec.get('next_watering', 'Tomorrow')}
                </div>
                <div style="margin-bottom: 0.3rem; font-size: 0.95rem;">
                    <b>Suggested frequency:</b> {w_rec.get('frequency', 'Every 2 days')}
                </div>
                <div style="margin-bottom: 0.3rem; font-size: 0.95rem;">
                    <b>Suggested amount:</b> {w_rec.get('amount_display', 'Approximately 500 ml')}
                </div>
                <div style="background: #e1f5fe; padding: 0.8rem; border-radius: 8px; font-size: 0.85rem; line-height: 1.4; color: #01579b; margin-top: 6px;">
                    <b>Reason:</b> {w_rec.get('reason', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("⚙️ Edit or Delete this Plant"):
        e1, e2 = st.columns([8, 4])
        with e1:
            with st.form("edit_plant_form"):
                e_name = st.text_input("Plant Name", value=current_plant['name'])
                e_type = st.selectbox("Plant Type", ["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"], index=["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"].index(current_plant['plant_type']) if current_plant['plant_type'] in ["Tomato", "Basil", "Mint", "Chili", "Pepper", "Lettuce", "Spinach", "Coriander", "Succulent", "Other"] else 0)
                e_variety = st.text_input("Variety", value=current_plant['variety'])
                e_loc = st.selectbox("Location", ["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"], index=["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"].index(current_plant['location']) if current_plant['location'] in ["Balcony", "Terrace", "Kitchen Sill", "Indoor Grow Tent", "Raised Garden Bed"] else 0)
                e_stage = st.selectbox("Growth Stage", ["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"], index=["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"].index(current_plant['growth_stage']) if current_plant['growth_stage'] in ["Seedling", "Vegetative", "Growing", "Flowering", "Fruiting", "Mature"] else 2)
                e_status = st.selectbox("Health Status", ["Healthy", "Needs Attention", "Critical"], index=["Healthy", "Needs Attention", "Critical"].index(current_plant['health_status']) if current_plant['health_status'] in ["Healthy", "Needs Attention", "Critical"] else 0)
                
                if st.form_submit_button("Update Plant Details"):
                    db.update_plant(current_plant['id'], e_name, e_type, e_variety, e_loc, current_plant['planting_date'], e_stage, e_status, user_id=current_user_id)
                    st.success("Plant details updated!")
                    st.rerun()
        with e2:
            st.markdown("### Danger Zone")
            if st.button("🗑 Delete Plant", type="secondary"):
                db.delete_plant(current_plant['id'], user_id=current_user_id)
                st.warning("Plant deleted.")
                navigate_to("📊 Dashboard")
                st.rerun()


# =========================================================
# 4. SMART WATERING SCHEDULE (Crop-by-Crop)
# =========================================================
elif st.session_state["nav_page"] == "💧 Smart Watering":
    st.markdown("""
    <div class="app-header">
        <h1>💧 Smart Watering & Micro-Climate Irrigation</h1>
        <p>Scientific moisture scheduling adapted to plant biology, growth stage, and atmospheric conditions</p>
    </div>
    """, unsafe_allow_html=True)
    
    plants = db.get_all_plants(user_id=current_user_id)
    w_info = weather_svc.get_current_weather()
    
    col_w1, col_w2 = st.columns([4, 8])
    with col_w1:
        st.markdown(f"""
        <div class="card-box">
            <div class="card-header">🌤 Active Climate Input</div>
            <div>🌡 <b>Temperature:</b> {w_info['temperature']}°C</div>
            <div>⛅ <b>Condition:</b> {w_info['condition']}</div>
            <div>💧 <b>Humidity:</b> {w_info['humidity']}%</div>
            <div>🌧 <b>Rain Probability:</b> {w_info['rain_possibility']}%</div>
            <div style="font-size: 0.75rem; color: #666; margin-top: 8px;">{w_info.get('status_message', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown("### Crop-by-Crop Irrigation Schedule")
        if not plants:
            st.info("No plants in your garden roster yet. Add crops to see automated irrigation schedules.")
        else:
            for p in plants:
                rec = plant_svc.calculate_smart_watering(
                    plant_type=p['plant_type'],
                    growth_stage=p['growth_stage'],
                    temperature=w_info['temperature'],
                    weather_condition=w_info['condition'],
                    humidity=w_info['humidity'],
                    rain_possibility=w_info['rain_possibility'],
                    location=p['location'],
                    last_watered_date=p.get('last_watered_date')
                )
                
                last_w_display = p.get('last_watered_date')[:16] if p.get('last_watered_date') else "Not logged yet"
                
                with st.container():
                    st.markdown(f"""
                    <div class="card-box" style="margin-bottom: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.15rem; font-weight: 700; color: #1565c0;">{get_plant_emoji(p['plant_type'])} {p['name']} ({p['plant_type']})</span>
                            <span style="font-weight: 600; color: #0277bd;">{rec['frequency']}</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 0.9rem;">
                            <b>Next Irrigation:</b> {rec['next_watering']} &nbsp;|&nbsp; 
                            <b>Suggested Amount:</b> {rec['amount_display']} &nbsp;|&nbsp;
                            <b>Last Watered:</b> {last_w_display}
                        </div>
                        <div style="background: #f1f8e9; padding: 6px 10px; border-radius: 6px; margin-top: 8px; font-size: 0.85rem; color: #2e7d32;">
                            <b>Agronomic Reason:</b> {rec['reason']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"💧 Log Watering for {p['name']}", key=f"water_btn_{p['id']}"):
                        db.log_watering(p['id'], amount_ml=rec['amount_ml'], notes="Logged via Smart Watering", user_id=current_user_id)
                        st.success(f"Watering logged for {p['name']}!")
                        st.rerun()


# =========================================================
# 5. WEATHER CONTEXT
# =========================================================
elif st.session_state["nav_page"] == "🌤 Weather":
    st.markdown("""
    <div class="app-header">
        <h1>🌤 Micro-Climate Weather Station</h1>
        <p>Live meteorological monitoring & container gardening transpiration impact</p>
    </div>
    """, unsafe_allow_html=True)
    
    w_info = weather_svc.get_current_weather()
    
    w_c1, w_c2, w_c3, w_c4 = st.columns(4)
    with w_c1:
        st.markdown(f"""
        <div class="stat-card info">
            <div class="stat-label">Temperature</div>
            <div class="stat-num" style="color: #0288d1;">{w_info['temperature']}°C</div>
        </div>
        """, unsafe_allow_html=True)
    with w_c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Weather Condition</div>
            <div class="stat-num" style="font-size: 1.25rem; margin-top: 0.5rem;">{w_info['condition']}</div>
        </div>
        """, unsafe_allow_html=True)
    with w_c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Relative Humidity</div>
            <div class="stat-num" style="color: #2e7d32;">{w_info['humidity']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with w_c4:
        st.markdown(f"""
        <div class="stat-card alert">
            <div class="stat-label">Rain Probability</div>
            <div class="stat-num" style="color: #f57f17;">{w_info['rain_possibility']}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="card-box">
        <div class="card-header">📡 Connection Status</div>
        <p style="font-size: 1rem; margin: 0;"><b>Status:</b> {w_info['status_message']}</p>
        <p style="font-size: 0.85rem; color: #555; margin-top: 6px;">
            Location: <b>{w_info['city']}</b> &bull; Data Provider: Open-Meteo Public API
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card-box">
        <div class="card-header">🌱 Urban Gardening Advisory for Current Weather</div>
        <ul>
            <li><b>Evapotranspiration Factor:</b> High temperatures accelerate moisture loss from smaller containers (under 10 liters).</li>
            <li><b>Foliage Care:</b> High relative humidity combined with warm temperatures increases fungal risk (like Early Blight and Powdery Mildew). Water strictly at the soil base to keep leaf surfaces dry.</li>
            <li><b>Balcony Wind Exposure:</b> Containers exposed to direct breeze experience up to 25% faster topsoil drying than sheltered indoor pots.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# 6. HEALTH HISTORY (Isolated for current user)
# =========================================================
elif st.session_state["nav_page"] == "📊 Health History":
    st.markdown("""
    <div class="app-header">
        <h1>📊 Plant Health History & Scan Archive</h1>
        <p>Review past pathology scans, disease progression, and treatment outcomes</p>
    </div>
    """, unsafe_allow_html=True)
    
    plants = db.get_all_plants(user_id=current_user_id)
    if not plants:
        st.info("No plants registered in your garden yet.")
    else:
        p_filter = st.selectbox("Filter History by Plant:", ["All Plants"] + [f"{p['name']} (ID: {p['id']})" for p in plants])
        
        if p_filter == "All Plants":
            history_items = db.get_recent_analyses(limit=25, user_id=current_user_id)
        else:
            sel_id = int(p_filter.split("ID: ")[1].replace(")", ""))
            history_items = db.get_plant_analyses(sel_id, user_id=current_user_id)
            
        if not history_items:
            st.info("No scan records found for this selection.")
        else:
            for hist in history_items:
                h_badge = "badge-attention" if "healthy" not in hist['disease'].lower() else "badge-healthy"
                with st.container():
                    st.markdown(f"""
                    <div class="card-box" style="margin-bottom: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; padding-bottom: 6px;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: #1b5e20;">🌱 {hist['plant_name']} &bull; Scan: {hist['created_at']}</span>
                            <span class="{h_badge}">{hist['disease']} — {hist['confidence']}%</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #444; margin-top: 6px;">
                            <b>Severity:</b> {hist['severity']} &nbsp;|&nbsp; 
                            <b>Image Reference:</b> {hist.get('image_path', 'leaf_scan.png')}
                        </div>
                        <div style="font-size: 0.85rem; color: #333; margin-top: 6px;">
                            <b>Visible Symptoms:</b>
                        </div>
                        <ul style="margin: 3px 0 6px 18px; font-size: 0.85rem;">
                            {''.join(f'<li>{s}</li>' for s in hist.get('symptoms', []))}
                        </ul>
                        <div style="font-size: 0.85rem; color: #333; margin-top: 4px;">
                            <b>Prescribed Treatments:</b>
                        </div>
                        <ul style="margin: 3px 0 0 18px; font-size: 0.85rem;">
                            {''.join(f'<li>{t}</li>' for t in hist.get('treatment', []))}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)


# =========================================================
# 7. NORMAL USER SEARCH HISTORY (Requirement 7 & 11)
# =========================================================
elif st.session_state["nav_page"] == "🔎 My Search History":
    st.markdown("""
    <div class="app-header">
        <h1>🔎 My Search History & Garden Knowledge</h1>
        <p>Search plant symptoms, care guides, and review your previous search queries</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns([8, 4])
    with col_s1:
        search_query = st.text_input("Search garden knowledge, plant symptoms, or crops:", placeholder="e.g. Early Blight, watering frequency, Roma tomato")
    with col_s2:
        search_type = st.selectbox("Search Type:", ["General Search", "Pathology & Disease", "Irrigation Guide", "Plant Varieties"])
        
    if st.button("🔍 Search & Log", type="primary"):
        if search_query.strip():
            db.log_search(user_id=current_user_id, query=search_query.strip(), search_type=search_type)
            st.success(f"Logged search for '{search_query.strip()}'. Results below:")
            
            # Simple contextual query matching
            q_clean = search_query.strip().lower()
            matching_plants = [p for p in user_plants if q_clean in p['name'].lower() or q_clean in p['plant_type'].lower() or q_clean in p['current_disease'].lower()]
            if matching_plants:
                st.markdown("#### 🌱 Matching Plants from Your Garden:")
                for mp in matching_plants:
                    st.write(f"- **{mp['name']}** ({mp['plant_type']}) - Status: {mp['health_status']}, Disease: {mp['current_disease']}")
            else:
                st.info(f"No direct plant match in your garden for '{search_query}'. You can find treatments in '🩺 Plant Doctor'.")
                
    st.markdown("---")
    st.markdown("### 📋 Your Recent Searches")
    my_searches = db.get_search_history(user_id=current_user_id, limit=50)
    if not my_searches:
        st.write("You have not performed any searches yet.")
    else:
        search_table_data = []
        for s in my_searches:
            search_table_data.append({
                "Search Query": s['query'],
                "Search Type": s.get('search_type', 'General'),
                "Date / Time": s['created_at']
            })
        st.dataframe(search_table_data, use_container_width=True)


# =========================================================
# 8. MASTER ADMIN DASHBOARD (Requirement 4)
# =========================================================
elif st.session_state["nav_page"] in ["👑 Master Admin Dashboard", "👑 Master Admin"]:
    if not is_master_admin:
        st.error("⛔ Access Denied. Master Admin privileges required.")
        st.session_state["nav_page"] = "📊 Dashboard"
        st.rerun()
    st.markdown("""
    <div class="admin-header">
        <h1>👑 Master Admin Dashboard</h1>
        <p>Platform-wide Analytics, Urban Farming Growth & System Status</p>
    </div>
    """, unsafe_allow_html=True)
    
    admin_stats = db.get_master_admin_stats()
    
    # 5 Dashboard Cards (Requirement 4: Total Users, Total Plants, Total Disease Scans, Total Searches, Active Users)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="stat-card purple">
            <div class="stat-label">Total Users</div>
            <div class="stat-num" style="color: #4a148c;">{admin_stats['total_users']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Plants</div>
            <div class="stat-num" style="color: #1b5e20;">{admin_stats['total_plants']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stat-card info">
            <div class="stat-label">Total Disease Scans</div>
            <div class="stat-num" style="color: #0288d1;">{admin_stats['total_analyses']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="stat-card alert">
            <div class="stat-label">Total Searches</div>
            <div class="stat-num" style="color: #f57f17;">{admin_stats['total_searches']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Users</div>
            <div class="stat-num" style="color: #2e7d32;">{admin_stats['active_users']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Navigation / Action Hub
    st.markdown("### ⚡ Quick Control Hub")
    h_col1, h_col2, h_col3 = st.columns(3)
    with h_col1:
        st.markdown("""
        <div class="card-box" style="text-align: center;">
            <div style="font-size: 2rem;">👥</div>
            <div style="font-weight: 700; margin: 6px 0; color: #1b5e20;">User Management</div>
            <p style="font-size: 0.85rem; color: #666;">Inspect registered gardeners, account roles, and account statuses.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open User Management 👥", use_container_width=True):
            st.session_state["nav_page"] = "👥 User Management"
            st.rerun()
    with h_col2:
        st.markdown("""
        <div class="card-box" style="text-align: center;">
            <div style="font-size: 2rem;">📋</div>
            <div style="font-weight: 700; margin: 6px 0; color: #0277bd;">User Activity Logs</div>
            <p style="font-size: 0.85rem; color: #666;">Monitor live system audits for authentication, plants, and care actions.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Activity Audit 📋", use_container_width=True):
            st.session_state["nav_page"] = "📋 User Activity"
            st.rerun()
    with h_col3:
        st.markdown("""
        <div class="card-box" style="text-align: center;">
            <div style="font-size: 2rem;">🔎</div>
            <div style="font-weight: 700; margin: 6px 0; color: #f57f17;">Search History Monitor</div>
            <p style="font-size: 0.85rem; color: #666;">Track global search queries and keyword trends across all users.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Search History 🔎", use_container_width=True):
            st.session_state["nav_page"] = "🔎 Global Search History"
            st.rerun()

    st.markdown("---")
    
    # Recent Activities Preview
    st.markdown("### ⏱ Recent System Events")
    recent_logs = db.get_activity_logs(limit=5)
    if not recent_logs:
        st.info("No system activity recorded yet.")
    else:
        for rlog in recent_logs:
            st.markdown(f"""
            <div class="activity-row">
                <div>
                    <b>{rlog.get('user_name') or 'User'}</b> ({rlog.get('user_email') or 'N/A'}): 
                    <span class="badge-user">{rlog.get('event_type', '').upper()}</span> 
                    <b>{rlog.get('event_name', '').replace('_', ' ').title()}</b>
                </div>
                <div style="font-size: 0.8rem; color: #888;">{rlog.get('created_at')}</div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# 8b. USER MANAGEMENT (Requirement 5)
# =========================================================
elif st.session_state["nav_page"] == "👥 User Management":
    if not is_master_admin:
        st.error("⛔ Access Denied. Master Admin privileges required.")
        st.session_state["nav_page"] = "📊 Dashboard"
        st.rerun()
    st.markdown("""
    <div class="admin-header">
        <h1>👥 User Management</h1>
        <p>Inspect all registered gardeners, manage roles, and review individual engagement metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    all_users = db.get_all_users_with_metrics()
    
    # Filters: Search by name/email, Role filter, Active/Inactive filter
    f_col1, f_col2, f_col3 = st.columns([6, 3, 3])
    with f_col1:
        filter_text = st.text_input("🔍 Search user by Name or Email:", "").strip().lower()
    with f_col2:
        filter_role = st.selectbox("Role Filter:", ["All Roles", "user", "master_admin"])
    with f_col3:
        filter_status = st.selectbox("Status Filter:", ["All Statuses", "Active Only", "Inactive Only"])
        
    filtered_users = []
    for u in all_users:
        if filter_text and (filter_text not in u['name'].lower() and filter_text not in u['email'].lower()):
            continue
        if filter_role != "All Roles" and u['role'] != filter_role:
            continue
        if filter_status == "Active Only" and not u['is_active']:
            continue
        if filter_status == "Inactive Only" and u['is_active']:
            continue
        filtered_users.append(u)
        
    if not filtered_users:
        st.info("No users match the selected filters.")
    else:
        # Table Columns: User ID, Name, Email, Role, Registration Date, Last Login, Plant Count, Disease Scan Count, Search Count, Status
        # NEVER display passwords or password hashes!
        user_table = []
        for u in filtered_users:
            status_str = "🟢 Active" if u['is_active'] else "🔴 Inactive"
            user_table.append({
                "User ID": u['id'],
                "Name": u['name'],
                "Email": u['email'],
                "Role": u['role'],
                "Registration Date": u['created_at'],
                "Last Login": u['last_login'] or "Never",
                "Plant Count": u.get('plants_count', 0),
                "Disease Scan Count": u.get('analyses_count', 0),
                "Search Count": u.get('searches_count', 0),
                "Status": status_str
            })
            
        st.dataframe(user_table, use_container_width=True)
        
        # User Action Controls (Activate / Deactivate)
        with st.expander("⚙️ Manage User Account Status"):
            user_select_map = {f"{u['name']} ({u['email']}) - ID: {u['id']}": u for u in filtered_users}
            target_label = st.selectbox("Select User to manage:", list(user_select_map.keys()))
            target_user = user_select_map[target_label]
            
            c_u1, c_u2 = st.columns(2)
            with c_u1:
                st.write(f"Current Status: **{'Active' if target_user['is_active'] else 'Inactive'}**")
                st.write(f"Assigned Role: **{target_user['role']}**")
            with c_u2:
                if target_user['email'].lower() != config.MASTER_ADMIN_EMAIL.lower():
                    if target_user['is_active']:
                        if st.button("🚫 Deactivate Account", key=f"deact_{target_user['id']}", type="secondary"):
                            db.toggle_user_active(target_user['id'], 0)
                            st.warning(f"User {target_user['email']} has been deactivated.")
                            st.rerun()
                    else:
                        if st.button("✅ Reactivate Account", key=f"react_{target_user['id']}"):
                            db.toggle_user_active(target_user['id'], 1)
                            st.success(f"User {target_user['email']} has been reactivated.")
                            st.rerun()
                else:
                    st.info("Master Admin account status cannot be deactivated.")



# =========================================================
# 9. USER ACTIVITY MONITOR (Requirement 6)
# =========================================================
elif st.session_state["nav_page"] == "📋 User Activity":
    if not is_master_admin:
        st.error("⛔ Access Denied. Master Admin privileges required.")
        st.session_state["nav_page"] = "📊 Dashboard"
        st.rerun()
    st.markdown("""
    <div class="admin-header">
        <h1>📋 User Activity Audit Monitor</h1>
        <p>Real-time audit log of all registration, authentication, agronomic, and search events</p>
    </div>
    """, unsafe_allow_html=True)
    
    all_users = db.get_all_users_with_metrics()
    user_choices = {"All Users": None}
    for u in all_users:
        user_choices[f"{u['name']} ({u['email']})"] = u['id']
        
    c_f1, c_f2, c_f3 = st.columns([5, 4, 3])
    with c_f1:
        sel_u_label = st.selectbox("Filter by User:", list(user_choices.keys()))
        selected_user_id = user_choices[sel_u_label]
    with c_f2:
        selected_event_type = st.selectbox("Event Category:", ["All", "auth", "plant", "disease", "watering", "search"])
    with c_f3:
        log_limit = st.selectbox("Entries to display:", [50, 100, 200], index=0)
        
    logs = db.get_activity_logs(user_id=selected_user_id, event_type=selected_event_type, limit=log_limit)
    
    if not logs:
        st.info("No activity records found matching the filters.")
    else:
        st.write(f"Showing **{len(logs)}** most recent activities (Newest first):")
        
        # Summary Table matching Requirement 6 columns
        act_summary = []
        for log in logs:
            act_summary.append({
                "User": log.get("user_name") or f"User #{log['user_id']}",
                "Email": log.get("user_email") or "N/A",
                "Activity": log.get("event_name", "").replace("_", " ").title(),
                "Date / Time": log.get("created_at"),
                "Details": (log.get("metadata")[:80] + "...") if len(log.get("metadata", "")) > 80 else log.get("metadata", "")
            })
        st.dataframe(act_summary, use_container_width=True)
        
        st.markdown("#### 🔍 Detailed Event Inspection")
        for log in logs:
            uname = log.get("user_name") or f"User #{log['user_id']}"
            uemail = log.get("user_email") or "N/A"
            etype = log.get("event_type", "general").upper()
            ename = log.get("event_name", "").replace("_", " ").title()
            
            with st.container():
                st.markdown(f"""
                <div class="activity-row">
                    <div>
                        <span style="font-weight: 700; color: #1b5e20;">👤 {uname}</span>
                        <span style="color: #666; font-size: 0.85rem; margin-left: 8px;">({uemail})</span>
                        <div style="font-size: 0.95rem; margin-top: 4px;">
                            <span class="badge-user">{etype}</span> &nbsp;
                            <b>Action:</b> {ename}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.8rem; color: #888;">⏱ {log['created_at']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if log.get("metadata"):
                    with st.expander(f"View Full Event Metadata ({ename})"):
                        try:
                            meta_obj = json.loads(log['metadata'])
                            st.json(meta_obj)
                        except Exception:
                            st.code(log['metadata'])



# =========================================================
# 10. MASTER ADMIN SEARCH HISTORY (Requirement 7)
# =========================================================
elif st.session_state["nav_page"] in ["🔎 Global Search History", "🔎 Search History"]:
    if not is_master_admin:
        st.error("⛔ Access Denied. Master Admin privileges required.")
        st.session_state["nav_page"] = "📊 Dashboard"
        st.rerun()
    st.markdown("""
    <div class="admin-header">
        <h1>🔎 Platform Search History Monitor</h1>
        <p>Global search activity across all registered users with keyword and date filters</p>
    </div>
    """, unsafe_allow_html=True)
    
    all_users = db.get_all_users_with_metrics()
    user_choices = {"All Users": None}
    for u in all_users:
        user_choices[f"{u['name']} ({u['email']})"] = u['id']
        
    s_col1, s_col2, s_col3 = st.columns([5, 4, 3])
    with s_col1:
        sel_u_label = st.selectbox("Filter by User:", list(user_choices.keys()), key="admin_sh_user")
        selected_user_id = user_choices[sel_u_label]
    with s_col2:
        search_kw = st.text_input("Filter by Keyword:", placeholder="e.g. Tomato, Blight, Water").strip()
    with s_col3:
        sort_order = st.selectbox("Date Sorting:", ["Newest First", "Oldest First"])
        
    order_desc = (sort_order == "Newest First")
    search_records = db.get_search_history(user_id=selected_user_id, keyword=search_kw, order_desc=order_desc, limit=100)
    
    if not search_records:
        st.info("No search history records found matching criteria.")
    else:
        st.write(f"Found **{len(search_records)}** search records:")
        sh_table = []
        for s in search_records:
            sh_table.append({
                "User": s.get("user_name") or f"User #{s['user_id']}",
                "Email": s.get("user_email") or "N/A",
                "Search Query": s['query'],
                "Search Type": s.get("search_type", "general").title(),
                "Date / Time": s['created_at']
            })
        st.dataframe(sh_table, use_container_width=True)


# =========================================================
# 11. SETTINGS & CONFIGURATION
# =========================================================
elif st.session_state["nav_page"] == "⚙️ Settings":
    st.markdown("""
    <div class="app-header">
        <h1>⚙️ Settings & Configuration</h1>
        <p>Manage Gemini API keys, local SQLite database, and profile settings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile Card
    st.markdown("### 👤 User Profile")
    role_badge = '<span class="badge-admin">👑 Master Admin</span>' if is_master_admin else '<span class="badge-user">🌱 Urban Gardener</span>'
    st.markdown(f"""
    <div class="card-box">
        <div style="font-size: 1.15rem; font-weight: 700; color: #1b5e20;">{current_user_name}</div>
        <div style="font-size: 0.9rem; color: #555; margin-top: 4px;">Email: <b>{current_email}</b></div>
        <div style="font-size: 0.9rem; color: #555; margin-top: 4px;">Role: {role_badge}</div>
        <div style="font-size: 0.9rem; color: #555; margin-top: 4px;">Authentication: <b>{st.session_state.get('logged_in_user', {}).get('auth_provider', 'local').title()}</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔑 Google Gemini API Key Configuration")
    st.write("Enter your Gemini API key to activate Gemini 1.5 Flash Vision for live image pathology. If left blank, the assistant automatically utilizes our built-in agronomic expert pathology engine.")
    
    curr_key = st.session_state.get("user_gemini_key", config.GEMINI_API_KEY)
    with st.form("gemini_key_form"):
        new_gemini_key = st.text_input("Gemini API Key:", value=curr_key, type="password")
        if st.form_submit_button("Save Key to Current Session"):
            st.session_state["user_gemini_key"] = new_gemini_key.strip()
            os.environ["GEMINI_API_KEY"] = new_gemini_key.strip()
            st.success("API key stored securely in session.")
            
    st.markdown("---")
    st.markdown("### 💾 SQLite Persistence Status")
    st.write(f"Database File: `{config.DB_PATH}`")
    st.write("All tables (`users`, `plants`, `plant_health`, `disease_analysis`, `watering_recommendations`, `care_tasks`, `weather_history`, `activity_logs`, `search_history`) persist across restarts.")
