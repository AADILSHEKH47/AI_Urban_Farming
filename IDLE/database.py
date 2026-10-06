"""
Database module for AI Urban Farming Assistant.
Uses SQLite for persistent local storage surviving application restarts.
Defines required tables:
- users (Phase 2 Authentication & Roles)
- activity_logs (Phase 2 Activity Auditing)
- search_history (Phase 2 Search Tracking)
- plants (with user_id isolation)
- plant_health
- disease_analysis (with user_id isolation)
- watering_recommendations
- care_tasks
- weather_history
- watering_logs
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional

import config

def get_connection():
    """Returns a SQLite connection with dict-like row factory."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes the database schema with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 0. Users table (Requirement 4)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            auth_provider TEXT DEFAULT 'local',
            provider_user_id TEXT DEFAULT '',
            password_hash TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Activity logs table (Requirement 4 & 8)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_name TEXT NOT NULL,
            metadata TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    # Search history table (Requirement 4 & 7)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            search_type TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    # 1. Plants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            plant_type TEXT NOT NULL,
            variety TEXT DEFAULT '',
            location TEXT DEFAULT 'Balcony',
            planting_date TEXT,
            growth_stage TEXT DEFAULT 'Growing',
            health_status TEXT DEFAULT 'Healthy',
            current_disease TEXT DEFAULT 'None',
            last_analysis_date TEXT,
            next_watering_date TEXT,
            last_watered_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    # Safe migrations for existing databases
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN user_id INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN last_watered_date TEXT")
    except Exception:
        pass
        
    # Watering logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watering_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            amount_ml INTEGER DEFAULT 500,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
        )
    """)
    
    # 2. Plant health table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plant_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            disease_name TEXT DEFAULT 'None',
            notes TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
        )
    """)
    
    # 3. Disease analysis table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disease_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            plant_id INTEGER NOT NULL,
            plant_name TEXT,
            disease TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            severity TEXT NOT NULL,
            symptoms_json TEXT,
            causes_json TEXT,
            treatment_json TEXT,
            prevention_json TEXT,
            image_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    try:
        cursor.execute("ALTER TABLE disease_analysis ADD COLUMN user_id INTEGER DEFAULT 1")
    except Exception:
        pass
    
    # 4. Watering recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watering_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            frequency TEXT NOT NULL,
            next_watering TEXT NOT NULL,
            amount_ml INTEGER DEFAULT 500,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
        )
    """)
    
    # 5. Care tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS care_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            task_description TEXT NOT NULL,
            task_type TEXT DEFAULT 'General',
            due_date TEXT,
            is_completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
        )
    """)
    
    # 6. Weather history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity INTEGER NOT NULL,
            condition TEXT NOT NULL,
            rain_possibility INTEGER DEFAULT 0,
            is_live INTEGER DEFAULT 1,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed default user if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (id, name, email, auth_provider, password_hash, role, created_at, is_active)
            VALUES (1, 'Urban Gardener (Default)', 'user@urbanfarming.com', 'local', '', 'user', datetime('now'), 1)
        """)
        
    # Safe migration for legacy records with NULL or invalid user_id:
    # Associate unassigned legacy records exclusively with the default user (id=1)
    cursor.execute("UPDATE plants SET user_id = 1 WHERE user_id IS NULL OR user_id <= 0")
    cursor.execute("UPDATE disease_analysis SET user_id = 1 WHERE user_id IS NULL OR user_id <= 0")
    cursor.execute("UPDATE search_history SET user_id = 1 WHERE user_id IS NULL OR user_id <= 0")

    # Seed Master Admin if not present, or safely migrate/reset password to Admin@12345
    import binascii, hashlib
    salt = binascii.hexlify(os.urandom(16)).decode("ascii")
    dk = hashlib.pbkdf2_hmac("sha256", "Admin@12345".encode("utf-8"), salt.encode("ascii"), 100000)
    admin_hash = f"pbkdf2:sha256:100000${salt}${binascii.hexlify(dk).decode('ascii')}"

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (config.MASTER_ADMIN_EMAIL.lower(),))
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute("""
            INSERT INTO users (name, email, auth_provider, password_hash, role, created_at, is_active)
            VALUES ('Master Admin', ?, 'local', ?, 'master_admin', datetime('now'), 1)
        """, (config.MASTER_ADMIN_EMAIL.lower(), admin_hash))
    else:
        # Safely migrate existing master admin to ensure the new password Admin@12345 and master_admin role
        cursor.execute("""
            UPDATE users SET password_hash = ?, role = 'master_admin', is_active = 1
            WHERE LOWER(email) = ?
        """, (admin_hash, config.MASTER_ADMIN_EMAIL.lower()))
    
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# User Accounts & Authentication CRUD (Requirement 1, 4, 5)
# -------------------------------------------------------------
def create_user(name: str, email: str, password_hash: str = "",
                auth_provider: str = "local", provider_user_id: str = "",
                role: str = "user") -> int:
    """Creates a new user record. Enforces unique email."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, auth_provider, provider_user_id, role, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 1)
    """, (name.strip(), email.strip().lower(), password_hash, auth_provider, provider_user_id, role))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user by id, returning dict without password_hash for safety."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, auth_provider, provider_user_id, role, created_at, last_login, is_active
        FROM users WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    """Fetches user by email."""
    conn = get_connection()
    cursor = conn.cursor()
    if include_password:
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    else:
        cursor.execute("""
            SELECT id, name, email, auth_provider, provider_user_id, role, created_at, last_login, is_active
            FROM users WHERE LOWER(email) = LOWER(?)
        """, (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_provider(auth_provider: str, provider_user_id: str) -> Optional[Dict[str, Any]]:
    """Fetches user by OAuth provider and provider user ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, auth_provider, provider_user_id, role, created_at, last_login, is_active
        FROM users WHERE auth_provider = ? AND provider_user_id = ?
    """, (auth_provider, provider_user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_last_login(user_id: int) -> bool:
    """Updates user last_login timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def update_user_role(user_id: int, role: str) -> bool:
    """Updates user role server-side."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def toggle_user_active(user_id: int, is_active: int) -> bool:
    """Toggles user active status (1 for active, 0 for inactive)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# -------------------------------------------------------------
# Activity Logging (Requirement 8)
# -------------------------------------------------------------
def log_activity(user_id: int, event_type: str, event_name: str, metadata: Any = "") -> int:
    """Logs user action to activity_logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    if isinstance(metadata, (dict, list)):
        meta_str = json.dumps(metadata)
    elif not isinstance(metadata, str):
        meta_str = str(metadata)
    else:
        meta_str = metadata
        
    cursor.execute("""
        INSERT INTO activity_logs (user_id, event_type, event_name, metadata, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (user_id, event_type, event_name, meta_str))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_activity_logs(user_id: Optional[int] = None, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches activity logs with optional user or event_type filtering."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT a.*, u.name AS user_name, u.email AS user_email
        FROM activity_logs a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
    """
    params = []
    if user_id is not None:
        query += " AND a.user_id = ?"
        params.append(user_id)
    if event_type and event_type != "All":
        query += " AND a.event_type = ?"
        params.append(event_type)
    query += " ORDER BY a.id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# -------------------------------------------------------------
# Search History (Requirement 4 & 7)
# -------------------------------------------------------------
def log_search(user_id: int, query: str, search_type: str = "general") -> int:
    """Logs user search query and records activity audit log."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO search_history (user_id, query, search_type, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, query.strip(), search_type))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Log to activity logs
    try:
        log_activity(
            user_id=user_id,
            event_type="search",
            event_name="search",
            metadata=json.dumps({"query": query.strip(), "search_type": search_type})
        )
    except Exception:
        pass
        
    return sid

def get_search_history(user_id: Optional[int] = None, keyword: Optional[str] = None, order_desc: bool = True, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves search history with optional user, keyword filtering and sorting."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.*, u.name AS user_name, u.email AS user_email
        FROM search_history s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE 1=1
    """
    params = []
    if user_id is not None:
        query += " AND s.user_id = ?"
        params.append(user_id)
    if keyword and keyword.strip():
        query += " AND (s.query LIKE ? OR u.name LIKE ? OR u.email LIKE ?)"
        kw = f"%{keyword.strip()}%"
        params.extend([kw, kw, kw])
    order = "DESC" if order_desc else "ASC"
    query += f" ORDER BY s.id {order} LIMIT ?"
    params.append(limit)
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# -------------------------------------------------------------
# Master Admin Analytics (Requirement 6)
# -------------------------------------------------------------
def get_master_admin_stats() -> Dict[str, Any]:
    """Computes platform-wide metrics for Master Admin."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM plants")
    total_plants = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM disease_analysis")
    total_analyses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM disease_analysis WHERE LOWER(disease) NOT LIKE '%healthy%'")
    total_diseases = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM search_history")
    total_searches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM plants WHERE health_status IN ('Needs Attention', 'Critical')")
    users_needing_attention = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_plants": total_plants,
        "total_analyses": total_analyses,
        "total_disease_detections": total_diseases,
        "total_searches": total_searches,
        "users_needing_attention": users_needing_attention
    }


def get_all_users_with_metrics() -> List[Dict[str, Any]]:
    """Fetches all users joined with their aggregate counts. No password hashes exposed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.auth_provider, u.role, u.created_at, u.last_login, u.is_active,
               COUNT(DISTINCT p.id) AS plants_count,
               COUNT(DISTINCT d.id) AS analyses_count,
               COUNT(DISTINCT s.id) AS searches_count
        FROM users u
        LEFT JOIN plants p ON p.user_id = u.id
        LEFT JOIN disease_analysis d ON d.user_id = u.id
        LEFT JOIN search_history s ON s.user_id = u.id
        GROUP BY u.id
        ORDER BY u.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# -------------------------------------------------------------
# Plant CRUD (with User Data Isolation)
# -------------------------------------------------------------
def add_plant(name: str, plant_type: str, variety: str = "", location: str = "Balcony",
              planting_date: str = "", growth_stage: str = "Growing", 
              health_status: str = "Healthy", user_id: int = 1) -> int:
    """Adds a new plant assigned to a user and registers initial health record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plants (name, plant_type, variety, location, planting_date, growth_stage, health_status, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (name, plant_type, variety, location, planting_date, growth_stage, health_status, user_id))
    plant_id = cursor.lastrowid
    
    # Add initial health record in plant_health
    cursor.execute("""
        INSERT INTO plant_health (plant_id, status, disease_name, notes)
        VALUES (?, ?, 'None', 'Initial registration')
    """, (plant_id, health_status))
    
    # Add initial default care task
    cursor.execute("""
        INSERT INTO care_tasks (plant_id, task_description, task_type, due_date)
        VALUES (?, ?, 'Watering', date('now', '+1 day'))
    """, (plant_id, f"Check soil moisture and inspect {name} foliage"))
    
    conn.commit()
    conn.close()
    
    # Audit log
    try:
        log_activity(
            user_id=user_id,
            event_type="plant",
            event_name="plant_added",
            metadata=json.dumps({"plant_id": plant_id, "name": name, "plant_type": plant_type})
        )
    except Exception:
        pass
        
    return plant_id

def get_all_plants(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Returns list of plants. If user_id is provided, isolates data for that user."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM plants WHERE user_id = ? ORDER BY id DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM plants ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_plant_by_id(plant_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single plant by ID with optional user authorization check."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM plants WHERE id = ? AND user_id = ?", (plant_id, user_id))
    else:
        cursor.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Alias for backwards compatibility
get_plant = get_plant_by_id

def update_plant(plant_id: int, name: str, plant_type: str, variety: str, 
                 location: str, planting_date: str, growth_stage: str, 
                 health_status: str, user_id: Optional[int] = None) -> bool:
    """Updates an existing plant's metadata with user authorization check."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("""
            UPDATE plants 
            SET name = ?, plant_type = ?, variety = ?, location = ?, 
                planting_date = ?, growth_stage = ?, health_status = ?,
                updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
        """, (name, plant_type, variety, location, planting_date, growth_stage, health_status, plant_id, user_id))
    else:
        cursor.execute("""
            UPDATE plants 
            SET name = ?, plant_type = ?, variety = ?, location = ?, 
                planting_date = ?, growth_stage = ?, health_status = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (name, plant_type, variety, location, planting_date, growth_stage, health_status, plant_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        try:
            log_activity(
                user_id=user_id if user_id is not None else 1,
                event_type="plant",
                event_name="plant_updated",
                metadata=json.dumps({"plant_id": plant_id, "name": name})
            )
        except Exception:
            pass
            
    return affected > 0

def delete_plant(plant_id: int, user_id: Optional[int] = None) -> bool:
    """Deletes a plant and cascades to all related tables with authorization check."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM plants WHERE id = ? AND user_id = ?", (plant_id, user_id))
    else:
        cursor.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        try:
            log_activity(
                user_id=user_id if user_id is not None else 1,
                event_type="plant",
                event_name="plant_deleted",
                metadata=json.dumps({"plant_id": plant_id})
            )
        except Exception:
            pass
            
    return affected > 0

# -------------------------------------------------------------
# Disease Analysis & Health Updates
# -------------------------------------------------------------
def save_disease_analysis(plant_id: int, plant_name: str, disease: str, confidence: int,
                          severity: str, symptoms: List[str], causes: List[str],
                          treatment: List[str], prevention: List[str],
                          image_path: str = "", user_id: int = 1) -> int:
    """Saves a disease analysis scan to disease_analysis table with user ownership."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO disease_analysis
        (plant_id, plant_name, disease, confidence, severity, symptoms_json, causes_json, treatment_json, prevention_json, image_path, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plant_id, plant_name, disease, confidence, severity,
        json.dumps(symptoms), json.dumps(causes), json.dumps(treatment), json.dumps(prevention),
        image_path, user_id
    ))
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Audit log
    try:
        log_activity(
            user_id=user_id,
            event_type="disease",
            event_name="disease_scan",
            metadata=json.dumps({"plant_id": plant_id, "plant_name": plant_name, "disease": disease, "confidence": confidence, "severity": severity})
        )
    except Exception:
        pass
        
    return analysis_id


def update_plant_health(plant_id: int, health_status: str, disease: str, next_watering: str = "") -> bool:
    """Updates plant status and logs health change in plant_health table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE plants
        SET health_status = ?,
            current_disease = ?,
            last_analysis_date = datetime('now'),
            next_watering_date = CASE WHEN ? != '' THEN ? ELSE next_watering_date END,
            updated_at = datetime('now')
        WHERE id = ?
    """, (health_status, disease, next_watering, next_watering, plant_id))
    
    cursor.execute("""
        INSERT INTO plant_health (plant_id, status, disease_name, notes)
        VALUES (?, ?, ?, datetime('now'))
    """, (plant_id, health_status, disease))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_plant_analyses(plant_id: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves all past analyses for a specific plant."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM disease_analysis WHERE plant_id = ? AND user_id = ? ORDER BY id DESC", (plant_id, user_id))
    else:
        cursor.execute("SELECT * FROM disease_analysis WHERE plant_id = ? ORDER BY id DESC", (plant_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item['symptoms'] = json.loads(item['symptoms_json']) if item['symptoms_json'] else []
        item['causes'] = json.loads(item['causes_json']) if item['causes_json'] else []
        item['treatment'] = json.loads(item['treatment_json']) if item['treatment_json'] else []
        item['prevention'] = json.loads(item['prevention_json']) if item['prevention_json'] else []
        results.append(item)
    return results

def get_recent_analyses(limit: int = 5, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves recent scans across plants (filtered by user_id if provided)."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM disease_analysis WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    else:
        cursor.execute("SELECT * FROM disease_analysis ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item['symptoms'] = json.loads(item['symptoms_json']) if item['symptoms_json'] else []
        item['causes'] = json.loads(item['causes_json']) if item['causes_json'] else []
        item['treatment'] = json.loads(item['treatment_json']) if item['treatment_json'] else []
        item['prevention'] = json.loads(item['prevention_json']) if item['prevention_json'] else []
        results.append(item)
    return results

# -------------------------------------------------------------
# Watering Recommendations & Care Tasks
# -------------------------------------------------------------
def save_watering_recommendation(plant_id: int, frequency: str, next_watering: str,
                                 amount_ml: int, reason: str) -> int:
    """Saves a watering recommendation to SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watering_recommendations (plant_id, frequency, next_watering, amount_ml, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (plant_id, frequency, next_watering, amount_ml, reason))
    rec_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rec_id

def get_latest_watering_recommendation(plant_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves the latest watering recommendation for a plant."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watering_recommendations WHERE plant_id = ? ORDER BY id DESC LIMIT 1", (plant_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_recent_watering_recommendations(limit: int = 5, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves the latest watering recommendations joined with plant details."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("""
            SELECT w.*, p.name AS plant_name, p.plant_type, p.location
            FROM watering_recommendations w
            JOIN plants p ON w.plant_id = p.id
            WHERE p.user_id = ?
            ORDER BY w.id DESC LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT w.*, p.name AS plant_name, p.plant_type, p.location
            FROM watering_recommendations w
            JOIN plants p ON w.plant_id = p.id
            ORDER BY w.id DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_watering(plant_id: int, amount_ml: int = 500, notes: str = "Regular watering", user_id: Optional[int] = None) -> int:
    """Logs a watering event, updates last_watered_date in plants table, and records activity log."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watering_logs (plant_id, amount_ml, notes)
        VALUES (?, ?, ?)
    """, (plant_id, amount_ml, notes))
    log_id = cursor.lastrowid
    
    # Query user_id if not explicitly provided
    uid = user_id
    if uid is None:
        cursor.execute("SELECT user_id FROM plants WHERE id = ?", (plant_id,))
        p_row = cursor.fetchone()
        if p_row:
            uid = p_row[0]
            
    cursor.execute("""
        UPDATE plants
        SET last_watered_date = datetime('now'),
            updated_at = datetime('now')
        WHERE id = ?
    """, (plant_id,))
    conn.commit()
    conn.close()
    
    # Audit log
    if uid:
        try:
            log_activity(
                user_id=uid,
                event_type="watering",
                event_name="watering_action",
                metadata=json.dumps({"plant_id": plant_id, "amount_ml": amount_ml, "notes": notes})
            )
        except Exception:
            pass
            
    return log_id

def add_care_task(plant_id: int, task_description: str, task_type: str = "General", due_date: str = "") -> int:
    """Adds a care task for a plant."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO care_tasks (plant_id, task_description, task_type, due_date)
        VALUES (?, ?, ?, ?)
    """, (plant_id, task_description, task_type, due_date or str(date.today())))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_active_care_tasks(limit: int = 10, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves pending care tasks joined with plant names."""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("""
            SELECT c.*, p.name AS plant_name, p.plant_type
            FROM care_tasks c
            JOIN plants p ON c.plant_id = p.id
            WHERE c.is_completed = 0 AND p.user_id = ?
            ORDER BY c.id DESC LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT c.*, p.name AS plant_name, p.plant_type
            FROM care_tasks c
            JOIN plants p ON c.plant_id = p.id
            WHERE c.is_completed = 0
            ORDER BY c.id DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_task_completed(task_id: int) -> bool:
    """Marks a care task as done."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE care_tasks SET is_completed = 1 WHERE id = ?", (task_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# -------------------------------------------------------------
# Weather History
# -------------------------------------------------------------
def log_weather(temp: float, humidity: int, condition: str, rain_possibility: int, is_live: bool):
    """Logs a weather snapshot to weather_history table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weather_history (temperature, humidity, condition, rain_possibility, is_live)
        VALUES (?, ?, ?, ?, ?)
    """, (temp, humidity, condition, rain_possibility, 1 if is_live else 0))
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# Dashboard Statistics (User Isolated)
# -------------------------------------------------------------
def get_dashboard_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Aggregates garden health and water metrics for dashboard (user-isolated if user_id given)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if user_id is not None:
        cursor.execute("SELECT COUNT(*) FROM plants WHERE user_id = ?", (user_id,))
        total_plants = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Healthy' AND user_id = ?", (user_id,))
        healthy_plants = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Needs Attention' AND user_id = ?", (user_id,))
        needs_attention = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Critical' AND user_id = ?", (user_id,))
        critical_plants = cursor.fetchone()[0]
        
        today_water_ml = total_plants * 500
        
        cursor.execute("SELECT name, next_watering_date FROM plants WHERE next_watering_date IS NOT NULL AND user_id = ? ORDER BY updated_at DESC LIMIT 1", (user_id,))
        next_w_row = cursor.fetchone()
        next_watering = next_w_row['next_watering_date'] if next_w_row and next_w_row['next_watering_date'] else "Tomorrow morning"
        
        cursor.execute("SELECT * FROM disease_analysis WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        recent_disease_row = cursor.fetchone()
        recent_disease = dict(recent_disease_row) if recent_disease_row else None
    else:
        cursor.execute("SELECT COUNT(*) FROM plants")
        total_plants = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Healthy'")
        healthy_plants = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Needs Attention'")
        needs_attention = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants WHERE health_status = 'Critical'")
        critical_plants = cursor.fetchone()[0]
        
        today_water_ml = total_plants * 500
        
        cursor.execute("SELECT name, next_watering_date FROM plants WHERE next_watering_date IS NOT NULL ORDER BY updated_at DESC LIMIT 1")
        next_w_row = cursor.fetchone()
        next_watering = next_w_row['next_watering_date'] if next_w_row and next_w_row['next_watering_date'] else "Tomorrow morning"
        
        cursor.execute("SELECT * FROM disease_analysis ORDER BY id DESC LIMIT 1")
        recent_disease_row = cursor.fetchone()
        recent_disease = dict(recent_disease_row) if recent_disease_row else None
        
    conn.close()
    
    return {
        "total_plants": total_plants,
        "healthy_plants": healthy_plants,
        "needs_attention": needs_attention,
        "critical_plants": critical_plants,
        "today_water_requirement_ml": today_water_ml,
        "next_watering": next_watering,
        "recent_disease": recent_disease
    }

# Ensure DB initialized on module load
init_db()
