import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    """SQLite database for login anomaly data persistence"""
    
    def __init__(self, db_path: str = "anomaly_detection.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Logins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_hour INTEGER,
                failed_attempts INTEGER,
                device_type INTEGER,
                location_code INTEGER,
                login_frequency INTEGER,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id INTEGER,
                prediction INTEGER,
                decision_score REAL,
                risk_score REAL,
                risk_level TEXT,
                is_anomaly BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (login_id) REFERENCES logins(id)
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                severity TEXT,
                message TEXT,
                alert_sent BOOLEAN DEFAULT 0,
                alert_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                details TEXT,
                user_action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Feature importance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_importance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                feature_name TEXT,
                importance_score REAL,
                feature_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_login(self, login_data: Dict) -> int:
        """Add a login record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO logins 
            (login_hour, failed_attempts, device_type, location_code, login_frequency, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            login_data['login_hour'],
            login_data['failed_attempts'],
            login_data['device_type'],
            login_data['location_code'],
            login_data['login_frequency'],
            login_data['latitude'],
            login_data['longitude']
        ))
        
        conn.commit()
        login_id = cursor.lastrowid
        conn.close()
        return login_id
    
    def add_prediction(self, prediction_data: Dict) -> int:
        """Add a prediction record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions
            (login_id, prediction, decision_score, risk_score, risk_level, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            prediction_data['login_id'],
            prediction_data['prediction'],
            prediction_data['decision_score'],
            prediction_data['risk_score'],
            prediction_data['risk_level'],
            prediction_data['is_anomaly']
        ))
        
        conn.commit()
        pred_id = cursor.lastrowid
        conn.close()
        return pred_id
    
    def add_alert(self, alert_data: Dict) -> int:
        """Add an alert record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts
            (prediction_id, severity, message, alert_type)
            VALUES (?, ?, ?, ?)
        """, (
            alert_data['prediction_id'],
            alert_data['severity'],
            alert_data['message'],
            alert_data['alert_type']
        ))
        
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        return alert_id
    
    def add_feature_importance(self, feature_data: List[Dict]) -> None:
        """Add feature importance records for SHAP analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for feature in feature_data:
            cursor.execute("""
                INSERT INTO feature_importance
                (prediction_id, feature_name, importance_score, feature_value)
                VALUES (?, ?, ?, ?)
            """, (
                feature['prediction_id'],
                feature['feature_name'],
                feature['importance_score'],
                feature['feature_value']
            ))
        
        conn.commit()
        conn.close()
    
    def add_audit_log(self, action: str, details: str, user_action: str = "system") -> None:
        """Add audit log entry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs
            (action, details, user_action)
            VALUES (?, ?, ?)
        """, (action, details, user_action))
        
        conn.commit()
        conn.close()
    
    def get_anomalies(self, limit: int = 100) -> List[Dict]:
        """Get recent anomalies"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                l.*, p.prediction, p.decision_score, p.risk_score, p.risk_level, p.created_at as pred_time
            FROM logins l
            JOIN predictions p ON l.id = p.login_id
            WHERE p.is_anomaly = 1
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM logins")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as anomalies FROM predictions WHERE is_anomaly = 1")
        anomalies = cursor.fetchone()['anomalies']
        
        cursor.execute("SELECT COUNT(*) as alerts_sent FROM alerts WHERE alert_sent = 1")
        alerts_sent = cursor.fetchone()['alerts_sent']
        
        conn.close()
        
        return {
            'total_logins': total,
            'anomalies_detected': anomalies,
            'alerts_sent': alerts_sent,
            'anomaly_rate': round(100 * anomalies / max(total, 1), 2)
        }
    
    def mark_alert_sent(self, alert_id: int) -> None:
        """Mark alert as sent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts SET alert_sent = 1 WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()
    
    def get_unsent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get alerts that haven't been sent yet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM alerts 
            WHERE alert_sent = 0 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
