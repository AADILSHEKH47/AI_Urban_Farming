"""
Authentication and Authorization Service for AI Urban Farming Assistant.
Handles:
- Secure password hashing (bcrypt with PBKDF2-SHA256 fallback)
- User registration & login with server-side role assignment
- Google OAuth and Facebook OAuth workflows
- Activity audit logging
- Master Admin verification
"""

import os
import re
import hmac
import hashlib
import binascii
import requests
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

import config
import database as db

# Try importing bcrypt for state-of-the-art password hashing
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# -------------------------------------------------------------
# Password Hashing & Verification (Requirement 1)
# -------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes a password securely using bcrypt or PBKDF2-SHA256."""
    if not password:
        return ""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        # Standard library PBKDF2-SHA256 with 100,000 iterations and random salt
        salt = binascii.hexlify(os.urandom(16)).decode("ascii")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100000)
        hash_hex = binascii.hexlify(dk).decode("ascii")
        return f"pbkdf2:sha256:100000${salt}${hash_hex}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plain-text password against a stored hash."""
    if not password or not stored_hash:
        return False
        
    # Check if hash is bcrypt
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$") or stored_hash.startswith("$2y$"):
        if HAS_BCRYPT:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False
        else:
            return False
            
    # Check if hash is PBKDF2 format
    if stored_hash.startswith("pbkdf2:"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                header, salt, expected_hash = parts
                iter_count = int(header.split(":")[2])
                dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), iter_count)
                actual_hash = binascii.hexlify(dk).decode("ascii")
                return hmac.compare_digest(actual_hash, expected_hash)
        except Exception:
            return False
            
    return False

# -------------------------------------------------------------
# User Registration & Login (Requirement 1 & 5)
# -------------------------------------------------------------
def register_user(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registers a new user account.
    Server-side assigns role:
    - If email matches MASTER_ADMIN_EMAIL: role = "master_admin"
    - Otherwise: role = "user"
    Normal users CANNOT specify or change their role.
    """
    name_clean = (name or "").strip()
    email_clean = (email or "").strip().lower()
    
    if not name_clean:
        return False, "Please enter your full name.", None
        
    if not email_clean or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email_clean):
        return False, "Please enter a valid email address.", None
        
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long.", None
        
    if password != confirm_password:
        return False, "Passwords do not match.", None
        
    # Prevent public registration using MASTER_ADMIN_EMAIL
    if email_clean == config.MASTER_ADMIN_EMAIL.lower():
        return False, "This email is reserved for the Master Admin. Please use the Master Admin credentials.", None

    # Check if email is already registered
    existing = db.get_user_by_email(email_clean)
    if existing:
        return False, f"An account with email '{email_clean}' is already registered. Please log in.", None
        
    role = "user"
        
    pwd_hash = hash_password(password)
    user_id = db.create_user(
        name=name_clean,
        email=email_clean,
        password_hash=pwd_hash,
        auth_provider="local",
        role=role
    )
    
    # Log registration activity
    db.log_activity(
        user_id=user_id,
        event_type="auth",
        event_name="register",
        metadata=json_dumps({"provider": "local", "role": role})
    )
    
    user = db.get_user_by_id(user_id)
    return True, f"Account created successfully as {role.replace('_', ' ').title()}!", user

def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates a user via local credentials.
    Server-side verifies master_admin role if email matches MASTER_ADMIN_EMAIL.
    """
    email_clean = (email or "").strip().lower()
    if not email_clean or not password:
        return False, "Please enter both email and password.", None
        
    user_record = db.get_user_by_email(email_clean, include_password=True)
    if not user_record:
        return False, "No account found with this email. Please register first.", None
        
    if not user_record.get("is_active", 1):
        return False, "This account has been deactivated. Please contact administration.", None
        
    stored_hash = user_record.get("password_hash", "")
    if not verify_password(password, stored_hash):
        return False, "Incorrect password. Please try again.", None
        
    user_id = user_record["id"]
    
    # Server-side Master Admin verification:
    # If this email matches MASTER_ADMIN_EMAIL, ensure role is master_admin
    current_role = user_record.get("role", "user")
    if email_clean == config.MASTER_ADMIN_EMAIL.lower():
        if current_role != "master_admin":
            db.update_user_role(user_id, "master_admin")
            current_role = "master_admin"
            
    db.update_user_last_login(user_id)
    
    # Log activity
    db.log_activity(
        user_id=user_id,
        event_type="auth",
        event_name="login",
        metadata=json_dumps({"provider": "local", "role": current_role})
    )
    
    clean_user = db.get_user_by_id(user_id)
    return True, f"Welcome back, {clean_user['name']}!", clean_user

def logout_user(user_id: int):
    """Logs logout action."""
    if user_id:
        db.log_activity(
            user_id=user_id,
            event_type="auth",
            event_name="logout",
            metadata=json_dumps({"timestamp": datetime.now().isoformat()})
        )

# -------------------------------------------------------------
# Google OAuth Integration (Requirement 2)
# -------------------------------------------------------------
def get_google_auth_url() -> str:
    """Generates standard Google OAuth2 Authorization URL."""
    if not config.GOOGLE_CLIENT_ID:
        return ""
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    redirect = requests.utils.quote(config.GOOGLE_REDIRECT_URI, safe="")
    scope = requests.utils.quote("openid email profile", safe="")
    return (
        f"{base}?client_id={config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&state=google"
        f"&access_type=offline"
        f"&prompt=select_account"
    )


def handle_google_callback(code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Exchanges Google authorization code for tokens and user profile."""
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        return False, "Google OAuth credentials not configured in environment.", None
        
    try:
        token_endpoint = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        res = requests.post(token_endpoint, data=data, timeout=8.0)
        if res.status_code != 200:
            return False, f"Failed to exchange code with Google: {res.text}", None
            
        token_data = res.json()
        access_token = token_data.get("access_token")
        
        # Fetch Google user profile
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_res = requests.get(userinfo_endpoint, headers=headers, timeout=8.0)
        if user_res.status_code != 200:
            return False, "Failed to retrieve user profile from Google.", None
            
        profile = user_res.json()
        email = profile.get("email", "").lower().strip()
        name = profile.get("name", "Google User").strip()
        google_id = str(profile.get("id", ""))
        
        return _login_or_create_oauth_user(
            name=name,
            email=email,
            auth_provider="google",
            provider_user_id=google_id
        )
    except Exception as e:
        return False, f"Google OAuth Error: {str(e)}", None

# -------------------------------------------------------------
# Facebook OAuth Integration (Requirement 3)
# -------------------------------------------------------------
def get_facebook_auth_url() -> str:
    """Generates standard Facebook OAuth URL."""
    if not config.FACEBOOK_CLIENT_ID:
        return ""
    base = "https://www.facebook.com/v19.0/dialog/oauth"
    redirect = requests.utils.quote(config.FACEBOOK_REDIRECT_URI, safe="")
    scope = requests.utils.quote("email,public_profile", safe="")
    return (
        f"{base}?client_id={config.FACEBOOK_CLIENT_ID}"
        f"&redirect_uri={redirect}"
        f"&scope={scope}"
        f"&state=facebook"
    )


def handle_facebook_callback(code: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Exchanges Facebook code for token and user profile."""
    if not config.FACEBOOK_CLIENT_ID or not config.FACEBOOK_CLIENT_SECRET:
        return False, "Facebook OAuth credentials not configured in environment.", None
        
    try:
        token_endpoint = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "client_id": config.FACEBOOK_CLIENT_ID,
            "client_secret": config.FACEBOOK_CLIENT_SECRET,
            "redirect_uri": config.FACEBOOK_REDIRECT_URI,
            "code": code
        }
        res = requests.get(token_endpoint, params=params, timeout=8.0)
        if res.status_code != 200:
            return False, f"Failed to exchange code with Facebook: {res.text}", None
            
        token_data = res.json()
        access_token = token_data.get("access_token")
        
        # Fetch profile
        me_endpoint = "https://graph.facebook.com/me"
        me_params = {"fields": "id,name,email", "access_token": access_token}
        user_res = requests.get(me_endpoint, params=me_params, timeout=8.0)
        if user_res.status_code != 200:
            return False, "Failed to retrieve user profile from Facebook.", None
            
        profile = user_res.json()
        fb_id = str(profile.get("id", ""))
        name = profile.get("name", "Facebook User").strip()
        email = profile.get("email", f"fb_{fb_id}@facebook.user").lower().strip()
        
        return _login_or_create_oauth_user(
            name=name,
            email=email,
            auth_provider="facebook",
            provider_user_id=fb_id
        )
    except Exception as e:
        return False, f"Facebook OAuth Error: {str(e)}", None

# -------------------------------------------------------------
# Internal OAuth Helper & Verification Simulator
# -------------------------------------------------------------
def _login_or_create_oauth_user(name: str, email: str, auth_provider: str, provider_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers or updates a user from an authenticated OAuth identity."""
    if not email:
        return False, "OAuth provider did not return an email address.", None
        
    existing = db.get_user_by_email(email)
    role = "master_admin" if email.lower() == config.MASTER_ADMIN_EMAIL.lower() else "user"
    
    if existing:
        user_id = existing["id"]
        # If user matches MASTER_ADMIN_EMAIL, ensure server-side promotion
        if email.lower() == config.MASTER_ADMIN_EMAIL.lower() and existing.get("role") != "master_admin":
            db.update_user_role(user_id, "master_admin")
        db.update_user_last_login(user_id)
    else:
        user_id = db.create_user(
            name=name,
            email=email,
            password_hash="",
            auth_provider=auth_provider,
            provider_user_id=provider_user_id,
            role=role
        )
        
    db.log_activity(
        user_id=user_id,
        event_type="auth",
        event_name=f"oauth_login_{auth_provider}",
        metadata=json_dumps({"provider": auth_provider, "provider_id": provider_user_id})
    )
    
    user = db.get_user_by_id(user_id)
    return True, f"Successfully authenticated via {auth_provider.title()}!", user

def json_dumps(data: Any) -> str:
    """Helper to safely serialize metadata."""
    import json
    try:
        return json.dumps(data)
    except Exception:
        return str(data)
