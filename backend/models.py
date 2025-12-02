import sqlite3
from datetime import datetime, date
from database import get_db_connection
from config import pwd_ctx, DEFAULT_WEAPONS


def get_user_by_username(username):
    """Get user by username"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()


def create_user(data):
    """Create a new user with full profile"""
    password_hash = pwd_ctx.hash(data['password'])
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO users 
                            (username, password_hash, email, first_name, last_name, 
                             phone, role, department) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (data['username'], password_hash, data['email'],
                           data.get('first_name', ''), data.get('last_name', ''),
                           data.get('phone', ''), data.get('role', 'guard'),
                           data.get('department', '')))
            user_id = cursor.lastrowid
            
            # Create default weapon preferences
            for weapon in DEFAULT_WEAPONS:
                cursor.execute('''INSERT INTO weapon_preferences 
                                (user_id, weapon_type, is_enabled) VALUES (?, ?, ?)''',
                              (user_id, weapon, True))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def delete_user(username):
    """Delete a user and all related data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        user = get_user_by_username(username)
        if user:
            user_id = user['id']
            cursor.execute('DELETE FROM weapon_preferences WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM detection_logs WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM daily_summary WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            return cursor.rowcount > 0
        return False


def update_password(username, new_password):
    """Update user password"""
    new_password_hash = pwd_ctx.hash(new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?',
                      (new_password_hash, username))
        conn.commit()
        return cursor.rowcount > 0


def update_user_profile(username, first_name, last_name, phone, department):
    """Update user profile information"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE users 
                         SET first_name = ?, last_name = ?, phone = ?, 
                             department = ?, updated_at = CURRENT_TIMESTAMP 
                         WHERE username = ?''',
                      (first_name, last_name, phone, department, username))
        conn.commit()
        return cursor.rowcount > 0


def log_detection(user_id, camera_id, weapon_type, confidence_score=0.85):
    """Log a weapon detection and update daily summary"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now()
        today = date.today()
        
        # Insert detection log
        cursor.execute('''INSERT INTO detection_logs 
                         (user_id, camera_id, weapon_type, confidence_score, detection_time, date_only) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (user_id, camera_id, weapon_type, confidence_score, now, today))
        
        # Update daily summary
        cursor.execute('''INSERT OR REPLACE INTO daily_summary 
                         (user_id, camera_id, detection_date, weapon_type, total_detections, 
                          avg_confidence, first_detection, last_detection)
                         SELECT ?, ?, ?, ?, 
                                COALESCE((SELECT total_detections FROM daily_summary 
                                         WHERE user_id = ? AND camera_id = ? AND detection_date = ? AND weapon_type = ?), 0) + 1,
                                (SELECT AVG(confidence_score) FROM detection_logs 
                                 WHERE user_id = ? AND camera_id = ? AND date_only = ? AND weapon_type = ?),
                                COALESCE((SELECT first_detection FROM daily_summary 
                                         WHERE user_id = ? AND camera_id = ? AND detection_date = ? AND weapon_type = ?), ?),
                                ?''',
                      (user_id, camera_id, today, weapon_type,
                       user_id, camera_id, today, weapon_type,
                       user_id, camera_id, today, weapon_type,
                       user_id, camera_id, today, weapon_type, now,
                       now))
        
        conn.commit()


def get_weapon_preferences(user_id):
    """Get weapon preferences for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT weapon_type, is_enabled FROM weapon_preferences 
                         WHERE user_id = ? ORDER BY weapon_type''', (user_id,))
        return cursor.fetchall()


def update_weapon_preferences(user_id, preferences):
    """Update weapon preferences"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for pref in preferences:
            weapon_type = pref.get('weapon_type')
            is_enabled = pref.get('is_enabled', True)
            
            cursor.execute('''UPDATE weapon_preferences 
                             SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP 
                             WHERE user_id = ? AND weapon_type = ?''',
                          (is_enabled, user_id, weapon_type))
        conn.commit()


def get_cameras_list():
    """Get all active cameras"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT id, camera_name, location, description, is_active 
                         FROM cameras WHERE is_active = TRUE ORDER BY camera_name''')
        return cursor.fetchall()


def get_detection_logs(camera_id=None, weapon_type=None, days=7, limit=100):
    """Get detection logs with filters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT dl.*, c.camera_name, c.location, u.username
            FROM detection_logs dl
            JOIN cameras c ON dl.camera_id = c.id
            JOIN users u ON dl.user_id = u.id
            WHERE dl.date_only >= date('now', '-{} days')
        '''.format(days)
        
        params = []
        
        if camera_id:
            query += ' AND dl.camera_id = ?'
            params.append(camera_id)
        
        if weapon_type:
            query += ' AND dl.weapon_type = ?'
            params.append(weapon_type)
        
        query += ' ORDER BY dl.detection_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()


def get_dashboard_data(user_id, days=7, camera_id=None):
    """Get dashboard data for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get daily summary
        query = '''
            SELECT ds.*, c.camera_name, c.location
            FROM daily_summary ds
            JOIN cameras c ON ds.camera_id = c.id
            WHERE ds.user_id = ? AND ds.detection_date >= date('now', '-{} days')
        '''.format(days)
        
        params = [user_id]
        
        if camera_id:
            query += ' AND ds.camera_id = ?'
            params.append(camera_id)
        
        query += ' ORDER BY ds.detection_date DESC, ds.weapon_type'
        
        cursor.execute(query, params)
        daily_data = cursor.fetchall()
        
        # Get weapon totals
        query2 = '''
            SELECT ds.weapon_type, SUM(ds.total_detections) as total, AVG(ds.avg_confidence) as avg_conf
            FROM daily_summary ds
            WHERE ds.user_id = ? AND ds.detection_date >= date('now', '-{} days')
        '''.format(days)
        
        params2 = [user_id]
        
        if camera_id:
            query2 += ' AND ds.camera_id = ?'
            params2.append(camera_id)
        
        query2 += ' GROUP BY ds.weapon_type ORDER BY total DESC'
        
        cursor.execute(query2, params2)
        weapon_totals = cursor.fetchall()
        
        # Get recent detections
        query3 = '''
            SELECT dl.*, c.camera_name, c.location
            FROM detection_logs dl
            JOIN cameras c ON dl.camera_id = c.id
            WHERE dl.user_id = ?
        '''
        
        params3 = [user_id]
        
        if camera_id:
            query3 += ' AND dl.camera_id = ?'
            params3.append(camera_id)
        
        query3 += ' ORDER BY dl.detection_time DESC LIMIT 20'
        
        cursor.execute(query3, params3)
        recent_detections = cursor.fetchall()
        
        return {
            "daily_summary": [dict(row) for row in daily_data],
            "weapon_totals": [dict(row) for row in weapon_totals],
            "recent_detections": [dict(row) for row in recent_detections]
        }


def get_public_current_detections(minutes=60):
    """Get current detections for public view"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.camera_name, c.location, 
                   dl.weapon_type, dl.confidence_score, dl.detection_time,
                   COUNT(*) as detection_count
            FROM detection_logs dl
            JOIN cameras c ON dl.camera_id = c.id
            WHERE dl.detection_time >= datetime('now', '-{} minutes')
            GROUP BY c.id, dl.weapon_type
            ORDER BY dl.detection_time DESC
        '''.format(minutes))
        return cursor.fetchall()


def get_public_camera_status():
    """Get camera status for public view"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.camera_name, c.location, c.is_active,
                   COUNT(dl.id) as detections_today,
                   MAX(dl.detection_time) as last_detection
            FROM cameras c
            LEFT JOIN detection_logs dl ON c.id = dl.camera_id 
                AND dl.date_only = date('now')
            GROUP BY c.id
            ORDER BY c.camera_name
        ''')
        return cursor.fetchall()