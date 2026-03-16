from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from database import Database
from risk_scoring import RiskScorer
from explainability import ModelExplainer, analyze_anomaly_patterns, get_feature_correlation_to_anomaly
from alerting import AlertManager
from auth import AuthDatabase, RoleChecker
import os

# Initialize components
app = FastAPI(
    title="AI Login Anomaly Detection API",
    description="Enterprise API for anomaly detection and threat intelligence",
    version="1.0.0"
)

# Security
auth_db = AuthDatabase()

# Dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify JWT token and return user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.replace("Bearer ", "")
    valid, payload = auth_db.verify_token(token)
    
    if not valid or not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

# Simple role checkers
def require_admin(user = Depends(get_current_user)):
    """Require admin role"""
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin role required")
    return user

def require_analyst_or_admin(user = Depends(get_current_user)):
    """Require analyst or admin role"""
    if user['role'] not in ['admin', 'analyst']:
        raise HTTPException(status_code=403, detail="Analyst or Admin role required")
    return user

# Load model
try:
    model = joblib.load('model.pkl')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Initialize components
db = Database()
risk_scorer = RiskScorer()
alert_manager = AlertManager()

# Feature names
FEATURE_NAMES = ['login_hour', 'failed_attempts', 'device_type', 'location_code', 
                 'login_frequency', 'latitude', 'longitude', 'travel_speed_mph']

# Initialize explainer if possible
explainer = None
try:
    # Load training data for explainability
    train_df = pd.read_csv('login_data.csv')
    X_train = train_df[FEATURE_NAMES].values
    explainer = ModelExplainer(model, X_train, FEATURE_NAMES)
    print("Explainer initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize explainer: {e}")

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginCredentials(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    login_hour: int
    failed_attempts: int
    device_type: int
    location_code: int
    login_frequency: int
    latitude: float
    longitude: float
    travel_speed_mph: float

class BulkPredictionRequest(BaseModel):
    logins: List[LoginRequest]

class PredictionResponse(BaseModel):
    prediction: str
    risk_score: float
    risk_level: str
    confidence: float
    decision_score: float
    attack_patterns: list
    explanation: Optional[Dict] = None
# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/login")
async def login(credentials: LoginCredentials):
    """
    Login and get JWT token
    
    Returns:
        token: JWT token for subsequent API calls
        username: Authenticated username
        role: User role
    """
    success, result = auth_db.authenticate(credentials.username, credentials.password)
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Get user info
    user = auth_db.get_user(credentials.username)
    
    return {
        'status': 'success',
        'token': result,
        'username': credentials.username,
        'role': user['role'],
        'message': 'Login successful'
    }

@app.get("/auth/profile")
async def get_profile(user = Depends(get_current_user)):
    """
    Get current user profile
    """
    return {
        'user_id': user['user_id'],
        'username': user['username'],
        'role': user['role'],
        'permissions': RoleChecker.get_permissions(user['role'])
    }

@app.post("/auth/logout")
async def logout(user = Depends(get_current_user)):
    """
    Logout and invalidate token
    """
    auth_db.logout(user['user_id'])
    
    return {
        'status': 'success',
        'message': 'Logged out successfully'
    }

# Admin endpoint to create users
@app.post("/auth/users")
async def create_user(
    username: str,
    password: str,
    email: str = None,
    role: str = "viewer",
    user = Depends(require_admin)
):
    """
    Create new user (admin only)
    """
    success, message = auth_db.create_user(username, password, email, role)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        'status': 'success',
        'username': username,
        'role': role,
        'message': 'User created successfully'
    }

# ============================================================================
# PREDICTION ENDPOINTS (PROTECTED)
# ============================================================================

@app.post("/api/v1/predict")
async def predict_login(
    login: LoginRequest,
    background_tasks: BackgroundTasks,
    user = Depends(require_analyst_or_admin)
):
    """
    Predict anomaly risk for a single login
    
    Returns risk assessment with explainability
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Store login in database
    login_id = db.add_login(login.dict())
    
    # Prepare features
    X = np.array([[
        login.login_hour,
        login.failed_attempts,
        login.device_type,
        login.location_code,
        login.login_frequency,
        login.latitude,
        login.longitude,
        login.travel_speed_mph
    ]])
    
    # Make prediction
    prediction = model.predict(X)[0]
    decision_score = model.decision_function(X)[0]
    
    # Calculate risk score
    risk_details, risk_level, overall_risk = risk_scorer.score_login(
        login.dict(), decision_score, prediction
    )
    
    # Store prediction in database
    pred_id = db.add_prediction({
        'login_id': login_id,
        'prediction': prediction,
        'decision_score': decision_score,
        'risk_score': overall_risk,
        'risk_level': risk_level,
        'is_anomaly': prediction == -1
    })
    
    # Get explanation
    explanation = None
    if explainer:
        try:
            explanation = explainer.explain_prediction(X)
            
            # Store feature importance
            feature_importance_data = []
            for feat in explanation['feature_importance']:
                feature_importance_data.append({
                    'prediction_id': pred_id,
                    'feature_name': feat['feature'],
                    'importance_score': feat['shap_value'],
                    'feature_value': feat['value']
                })
            
            if feature_importance_data:
                db.add_feature_importance(feature_importance_data)
        except Exception as e:
            print(f"Error generating explanation: {e}")
    
    # Create alert if anomaly
    if prediction == -1:
        alert = alert_manager.create_alert(pred_id, risk_details, login.dict())
        alert_id = db.add_alert({
            'prediction_id': pred_id,
            'severity': alert['severity'],
            'message': alert['message'],
            'alert_type': alert['alert_type']
        })
        
        # Send alert asynchronously
        if alert['should_alert']:
            background_tasks.add_task(
                alert_manager.send_slack_alert, alert
            )
            db.add_audit_log(
                'alert_created',
                f'Alert {alert_id} for login {login_id}',
                'system'
            )
    
    # Audit log
    db.add_audit_log(
        'prediction_made',
        f'Prediction {pred_id} for login {login_id}',
        'api'
    )
    
    return PredictionResponse(
        prediction='ANOMALY' if prediction == -1 else 'NORMAL',
        risk_score=overall_risk,
        risk_level=risk_level,
        confidence=risk_details['confidence'],
        decision_score=decision_score,
        attack_patterns=risk_details['attack_patterns'],
        explanation=explanation
    )

@app.post("/api/v1/bulk-predict")
async def bulk_predict(request: BulkPredictionRequest, user = Depends(require_analyst_or_admin)):
    """
    Batch predict for multiple logins
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    results = []
    for login in request.logins:
        X = np.array([[
            login.login_hour, login.failed_attempts, login.device_type,
            login.location_code, login.login_frequency, login.latitude, login.longitude, login.travel_speed_mph
        ]])
        
        prediction = model.predict(X)[0]
        decision_score = model.decision_function(X)[0]
        risk_details, risk_level, overall_risk = risk_scorer.score_login(
            login.dict(), decision_score, prediction
        )
        
        results.append({
            'login': login.dict(),
            'prediction': 'ANOMALY' if prediction == -1 else 'NORMAL',
            'risk_score': overall_risk,
            'risk_level': risk_level,
            'confidence': risk_details['confidence']
        })
    
    return {
        'total': len(results),
        'anomalies': sum(1 for r in results if r['prediction'] == 'ANOMALY'),
        'results': results
    }

# ============================================================================
# INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/threats")
async def get_active_threats(limit: int = Query(50, ge=1, le=500), user = Depends(require_analyst_or_admin)):
    """
    Get recent anomalies/threats
    """
    threats = db.get_anomalies(limit=limit)
    
    if not threats:
        return {
            'total': 0,
            'threats': [],
            'critical_count': 0,
            'high_count': 0
        }
    
    return {
        'total': len(threats),
        'threats': threats,
        'critical_count': sum(1 for t in threats if t.get('risk_level') == 'CRITICAL'),
        'high_count': sum(1 for t in threats if t.get('risk_level') == 'HIGH')
    }

@app.get("/api/v1/statistics")
async def get_statistics(user = Depends(require_analyst_or_admin)):
    """
    Get system statistics and metrics
    """
    stats = db.get_statistics()
    
    return {
        'timestamp': pd.Timestamp.now().isoformat(),
        'statistics': stats,
        'model_status': 'ready' if model else 'not_loaded',
        'explainer_status': 'ready' if explainer else 'unavailable'
    }

@app.get("/api/v1/feature-importance")
async def get_feature_importance(user = Depends(require_analyst_or_admin)):
    """
    Get global feature importance across all predictions
    """
    if not explainer or model is None:
        raise HTTPException(status_code=503, detail="Explainer not available")
    
    try:
        df = pd.read_csv('login_data.csv')
        X = df[FEATURE_NAMES].values
        predictions = model.predict(X)
        
        importance = explainer.get_feature_importance_scores(X)
        correlations = get_feature_correlation_to_anomaly(X, predictions, FEATURE_NAMES)
        
        return {
            'feature_importance': importance,
            'anomaly_correlations': correlations,
            'features': FEATURE_NAMES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/anomaly-patterns")
async def get_anomaly_patterns(user = Depends(require_analyst_or_admin)):
    """
    Analyze and return detected anomaly patterns
    """
    try:
        anomalies = db.get_anomalies(limit=100)
        
        if not anomalies:
            return {'patterns': {}, 'total_anomalies': 0}
        
        # Generate explanations for anomalies
        explanations = []
        for anomaly in anomalies:
            X = np.array([[
                anomaly['login_hour'],
                anomaly['failed_attempts'],
                anomaly['device_type'],
                anomaly['location_code'],
                anomaly['login_frequency'],
                anomaly['latitude'],
                anomaly['longitude'],
                anomaly.get('travel_speed_mph', 0)
            ]])
            
            if explainer:
                try:
                    exp = explainer.explain_prediction(X)
                    explanations.append(exp)
                except:
                    pass
        
        patterns = analyze_anomaly_patterns(explanations) if explanations else {}
        
        return {
            'patterns': patterns,
            'total_anomalies': len(anomalies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/report")
async def generate_report(days: int = Query(7, ge=1, le=90), user = Depends(require_admin)):
    """
    Generate intelligence report
    """
    stats = db.get_statistics()
    
    report = {
        'report_date': pd.Timestamp.now().isoformat(),
        'period_days': days,
        'summary': {
            'total_logins': stats['total_logins'],
            'anomalies_detected': stats['anomalies_detected'],
            'anomaly_rate_percent': stats['anomaly_rate'],
            'alerts_sent': stats['alerts_sent']
        },
        'status': 'Active monitoring' if stats['total_logins'] > 0 else 'No activity',
        'recommendations': [
            'Monitor geographic anomalies',
            'Review credential stuffing attempts',
            'Increase MFA for night logins'
        ] if stats['anomaly_rate'] > 5 else ['System operating normally']
    }
    
    return report

# ============================================================================
# HEALTH & FEEDBACK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        'status': 'healthy',
        'model_loaded': model is not None,
        'database_connected': True,
        'timestamp': pd.Timestamp.now().isoformat()
    }

@app.post("/api/v1/feedback")
async def submit_feedback(
    prediction_id: int,
    actual_label: str = Query(..., regex="^(true_positive|false_positive|true_negative|false_negative)$"),
    notes: Optional[str] = None,
    user = Depends(require_analyst_or_admin)
):
    """
    Submit feedback for model improvement
    """
    db.add_audit_log(
        'feedback_submitted',
        f'Prediction {prediction_id}: {actual_label}. Notes: {notes}',
        'analyst'
    )
    
    return {
        'status': 'feedback_received',
        'prediction_id': prediction_id,
        'label': actual_label,
        'timestamp': pd.Timestamp.now().isoformat()
    }

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """
    API root endpoint with documentation
    """
    return {
        'name': 'AI Login Anomaly Detection API',
        'version': '1.0.0',
        'endpoints': {
            'predictions': '/api/v1/predict (POST)',
            'bulk_predictions': '/api/v1/bulk-predict (POST)',
            'active_threats': '/api/v1/threats (GET)',
            'statistics': '/api/v1/statistics (GET)',
            'feature_importance': '/api/v1/feature-importance (GET)',
            'anomaly_patterns': '/api/v1/anomaly-patterns (GET)',
            'reports': '/api/v1/report (GET)',
            'feedback': '/api/v1/feedback (POST)',
            'health': '/health (GET)'
        },
        'documentation': '/docs',
        'database': 'SQLite (anomaly_detection.db)',
        'model': 'Isolation Forest'
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
