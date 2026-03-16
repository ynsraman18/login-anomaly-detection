import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import jwt

class AuthDatabase:
    """User authentication and session management"""
    
    def __init__(self, db_path: str = "auth.db"):
        self.db_path = db_path
        self.secret_key = "your-secret-key-change-this-in-production"
        self.init_db()
    
    def init_db(self):
        """Initialize authentication tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'analyst',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Sessions/tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
        if cursor.fetchone()[0] == 0:
            admin_hash = self.hash_password('admin123')
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ('admin', 'admin@anomaly.local', admin_hash, 'admin', 1))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, pwd_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = pwd_hash.split('$')
            pwd_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_check.hex() == hash_hex
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str, role: str = 'analyst') -> Tuple[bool, str]:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            pwd_hash = self.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (username, email, pwd_hash, role))
            
            conn.commit()
            conn.close()
            return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists"
        except Exception as e:
            return False, str(e)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Authenticate user and generate token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, password_hash, role, is_active 
                FROM users 
                WHERE username = ?
            """, (username,))
            
            result = cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            user_id, pwd_hash, role, is_active = result
            
            if not is_active:
                return False, "User account is inactive"
            
            if not self.verify_password(password, pwd_hash):
                return False, "Invalid password"
            
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (user_id,))
            conn.commit()
            
            # Generate token
            token = self.create_token(user_id, username, role)
            
            # Store session
            expires_at = datetime.now() + timedelta(hours=24)
            cursor.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token, expires_at))
            conn.commit()
            conn.close()
            
            return True, token
        except Exception as e:
            return False, str(e)
    
    def create_token(self, user_id: int, username: str, role: str) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT is_active FROM sessions 
                WHERE token = ? AND is_active = 1 AND expires_at > CURRENT_TIMESTAMP
            """, (token,))
            
            if not cursor.fetchone():
                return False, None
            
            conn.close()
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, None
        except:
            return False, None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user details"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users WHERE id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'is_active': result[4],
                'created_at': result[5],
                'last_login': result[6]
            }
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users WHERE username = ?
            """, (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'is_active': result[4],
                'created_at': result[5],
                'last_login': result[6]
            }
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def list_users(self) -> list:
        """Get all users (admin only)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users ORDER BY created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3],
                    'is_active': row[4],
                    'created_at': row[5],
                    'last_login': row[6]
                })
            
            conn.close()
            return users
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    
    def logout(self, token: str) -> bool:
        """Invalidate token/logout"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions SET is_active = 0 WHERE token = ?
            """, (token,))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            if not self.verify_password(old_password, result[0]):
                return False, "Current password is incorrect"
            
            new_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password_hash = ? WHERE id = ?
            """, (new_hash, user_id))
            
            conn.commit()
            conn.close()
            return True, "Password changed successfully"
        except Exception as e:
            return False, str(e)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET is_active = 0 WHERE id = ?
            """, (user_id,))
            
            cursor.execute("""
                UPDATE sessions SET is_active = 0 WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False


class RoleChecker:
    """Role-based access control"""
    
    ROLES = {
        'admin': ['view', 'predict', 'manage_users', 'download', 'configure', 'delete'],
        'analyst': ['view', 'predict', 'download', 'feedback'],
        'viewer': ['view']
    }
    
    @staticmethod
    def can_access(role: str, action: str) -> bool:
        """Check if role can perform action"""
        if role not in RoleChecker.ROLES:
            return False
        return action in RoleChecker.ROLES[role]
    
    @staticmethod
    def get_permissions(role: str) -> list:
        """Get all permissions for role"""
        return RoleChecker.ROLES.get(role, [])
