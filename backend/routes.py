import random
import requests
from flask import Blueprint, request, Response
from auth import create_token, verify_token, token_required, get_token_from_request, verify_password, hash_password
from models import (
    get_user_by_username, create_user, delete_user, update_password, update_user_profile,
    log_detection, get_weapon_preferences, update_weapon_preferences, get_cameras_list,
    get_detection_logs, get_dashboard_data, get_public_current_detections, get_public_camera_status
)
from config import AI_STREAM_URL, DEFAULT_WEAPONS

# Create blueprints
auth_bp = Blueprint('auth', __name__)
camera_bp = Blueprint('camera', __name__)
detection_bp = Blueprint('detection', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
public_bp = Blueprint('public', __name__)

# ========== AUTH ROUTES ==========
@auth_bp.post("/login")
def login():
    try:
        data = request.json
        if not data or not data.get("username") or not data.get("password"):
            return {"error": "Missing credentials"}, 400

        user = get_user_by_username(data["username"])
        if not user:
            return {"error": "Invalid credentials"}, 401
        
        if not verify_password(data["password"], user["password_hash"]):
            return {"error": "Invalid credentials"}, 401
        
        if not user["is_active"]:
            return {"error": "Account is deactivated"}, 403

        token = create_token(data["username"], user["id"], user["role"])
        
        return {
            "access_token": token,
            "username": data["username"],
            "role": user["role"],
            "full_name": f"{user['first_name']} {user['last_name']}"
        }
    except Exception as e:
        print(f"Login error: {e}")
        return {"error": "Internal server error"}, 500


@auth_bp.post("/register")
def register():
    try:
        data = request.json
        if not data or not data.get("username") or not data.get("password") or not data.get("email"):
            return {"error": "Missing required fields"}, 400
        
        username = data["username"].strip()
        password = data["password"]
        email = data["email"].strip()
        
        if len(username) < 3:
            return {"error": "Username must be at least 3 characters long"}, 400
        
        if len(password) < 6:
            return {"error": "Password must be at least 6 characters long"}, 400
        
        if '@' not in email:
            return {"error": "Invalid email address"}, 400
        
        if create_user(data):
            return {"message": "User created successfully"}, 201
        else:
            return {"error": "Username or email already exists"}, 409
    except Exception as e:
        print(f"Register error: {e}")
        return {"error": "Internal server error"}, 500


@auth_bp.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


@auth_bp.post("/change-password")
@token_required
def change_password():
    try:
        data = request.json
        if not data or not data.get("current_password") or not data.get("new_password"):
            return {"error": "Missing current_password or new_password"}, 400
        
        if len(data["new_password"]) < 6:
            return {"error": "New password must be at least 6 characters long"}, 400
        
        username = request.user.get('sub')
        user = get_user_by_username(username)
        
        if not user:
            return {"error": "User not found"}, 404
        
        if not verify_password(data["current_password"], user["password_hash"]):
            return {"error": "Current password is incorrect"}, 400
        
        if update_password(username, data["new_password"]):
            return {"message": "Password changed successfully"}
        else:
            return {"error": "Failed to update password"}, 500
    except Exception as e:
        print(f"Change password error: {e}")
        return {"error": "Internal server error"}, 500


@auth_bp.delete("/delete-account")
@token_required
def delete_account():
    try:
        username = request.user.get('sub')
        if delete_user(username):
            return {"message": "Account deleted successfully"}
        else:
            return {"error": "Account not found"}, 404
    except Exception as e:
        print(f"Delete account error: {e}")
        return {"error": "Internal server error"}, 500


@auth_bp.get("/user-info")
@token_required
def user_info():
    try:
        user = get_user_by_username(request.user.get('sub'))
        if user:
            return {
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "phone": user["phone"],
                "role": user["role"],
                "department": user["department"],
                "created_at": user["created_at"]
            }
        else:
            return {"error": "User not found"}, 404
    except Exception as e:
        print(f"User info error: {e}")
        return {"error": "Internal server error"}, 500


@auth_bp.put("/user-profile")
@token_required
def update_profile():
    try:
        data = request.json
        username = request.user.get('sub')
        
        if update_user_profile(username, data.get('first_name'), data.get('last_name'),
                              data.get('phone'), data.get('department')):
            return {"message": "Profile updated successfully"}
        else:
            return {"error": "Failed to update profile"}, 500
    except Exception as e:
        print(f"Update profile error: {e}")
        return {"error": "Internal server error"}, 500


# ========== CAMERA ROUTES ==========
@camera_bp.get("/cameras")
def cameras():
    try:
        cameras_list = get_cameras_list()
        return {"cameras": [dict(cam) for cam in cameras_list]}
    except Exception as e:
        print(f"Get cameras error: {e}")
        return {"error": "Internal server error"}, 500


# ========== WEAPON PREFERENCES ROUTES ==========
@detection_bp.get("/weapon-preferences")
@token_required
def get_prefs():
    try:
        user_id = request.user.get('user_id')
        prefs = get_weapon_preferences(user_id)
        
        if not prefs:
            # Create defaults
            from database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for weapon in DEFAULT_WEAPONS:
                    cursor.execute('''INSERT INTO weapon_preferences 
                                    (user_id, weapon_type, is_enabled) VALUES (?, ?, ?)''',
                                  (user_id, weapon, True))
                conn.commit()
            prefs = get_weapon_preferences(user_id)
        
        return {"preferences": [dict(pref) for pref in prefs]}
    except Exception as e:
        print(f"Get weapon preferences error: {e}")
        return {"error": "Internal server error"}, 500


@detection_bp.post("/weapon-preferences")
@token_required
def set_prefs():
    try:
        data = request.json
        if not data or 'preferences' not in data:
            return {"error": "Missing preferences data"}, 400
        
        user_id = request.user.get('user_id')
        update_weapon_preferences(user_id, data['preferences'])
        
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        print(f"Update weapon preferences error: {e}")
        return {"error": "Internal server error"}, 500


# ========== DETECTION ROUTES ==========
@detection_bp.post("/log-detection")
@token_required
def log_det():
    try:
        data = request.json
        if not data or not data.get('weapon_type') or not data.get('camera_id'):
            return {"error": "Missing weapon_type or camera_id"}, 400
        
        user_id = request.user.get('user_id')
        log_detection(user_id, data['camera_id'], data['weapon_type'], data.get('confidence_score', 0.85))
        
        return {"message": "Detection logged successfully"}
    except Exception as e:
        print(f"Log detection error: {e}")
        return {"error": "Internal server error"}, 500


@detection_bp.get("/detection-logs")
def get_logs():
    try:
        camera_id = request.args.get('camera_id', type=int)
        weapon_type = request.args.get('weapon_type')
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        logs = get_detection_logs(camera_id, weapon_type, days, limit)
        return {"logs": [dict(log) for log in logs]}
    except Exception as e:
        print(f"Get detection logs error: {e}")
        return {"error": "Internal server error"}, 500


# ========== DASHBOARD ROUTES ==========
@dashboard_bp.get("/dashboard-data")
@token_required
def dashboard():
    try:
        user_id = request.user.get('user_id')
        days = request.args.get('days', 7, type=int)
        camera_id = request.args.get('camera_id', type=int)
        
        data = get_dashboard_data(user_id, days, camera_id)
        return data
    except Exception as e:
        print(f"Dashboard data error: {e}")
        return {"error": "Internal server error"}, 500


# ========== PUBLIC ROUTES ==========
@public_bp.get("/current-detections")
def current_detections():
    try:
        minutes = request.args.get('minutes', 60, type=int)
        detections = get_public_current_detections(minutes)
        return {"detections": [dict(det) for det in detections]}
    except Exception as e:
        print(f"Public current detections error: {e}")
        return {"error": "Internal server error"}, 500


@public_bp.get("/camera-status")
def camera_status():
    try:
        cameras = get_public_camera_status()
        return {"cameras": [dict(cam) for cam in cameras]}
    except Exception as e:
        print(f"Public camera status error: {e}")
        return {"error": "Internal server error"}, 500


# ========== VIDEO STREAM ROUTE ==========
@camera_bp.get("/video")
def video_stream():
    try:
        token = request.args.get("token")
        camera_id = request.args.get("camera_id", 1, type=int)
        
        if not token or not verify_token(token):
            return {"error": "Unauthorized"}, 401

        user_data = verify_token(token)
        if user_data and random.random() < 0.1:
            weapons = DEFAULT_WEAPONS
            weapon = random.choice(weapons)
            confidence = random.uniform(0.7, 0.95)
            log_detection(user_data.get('user_id'), camera_id, weapon, confidence)

        r = requests.get(AI_STREAM_URL, stream=True)
        return Response(r.iter_content(chunk_size=1024),
                        content_type=r.headers.get("Content-Type", "multipart/x-mixed-replace; boundary=frame"))
    except Exception as e:
        print(f"Video proxy error: {e}")
        return {"error": "Internal server error"}, 500