API ENDPOINTS - DETAILED GUIDE
================================

These are the 10 REST API endpoints available for integrating your anomaly detection system
with external tools, SIEM platforms, or custom applications.

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 1: /api/v1/predict
────────────────────────────
METHOD: POST
PURPOSE: Analyze risk for a SINGLE login attempt in real-time

WHAT IT DOES:
- Takes login details as input
- Runs through ML model
- Calculates multi-dimensional risk score
- Generates SHAP explanation
- Stores in database
- Returns full risk assessment

INPUT (JSON body):
{
  "login_hour": 14,              # Hour of day (0-23)
  "failed_attempts": 2,          # Number of failed login attempts
  "device_type": 1,              # 0=mobile, 1=laptop, 2=tablet
  "location_code": 50,           # Location identifier (1-100)
  "login_frequency": 15,         # How many logins (1-200)
  "latitude": 40.7128,           # GPS latitude
  "longitude": -74.0060          # GPS longitude
}

OUTPUT (JSON response):
{
  "prediction": "NORMAL",                    # ANOMALY or NORMAL
  "risk_score": 18.5,                        # 0-100 scale
  "risk_level": "LOW",                       # CRITICAL/HIGH/MEDIUM/LOW/NORMAL
  "confidence": 87.3,                        # How confident (0-100%)
  "decision_score": -0.0521,                 # Raw ML score
  "attack_patterns": [
    {
      "name": "Credential Stuffing",
      "detected": false,
      "confidence": 0.95
    },
    {
      "name": "Night Attack",
      "detected": false,
      "confidence": 0.80
    },
    {
      "name": "Bot Activity",
      "detected": false,
      "confidence": 0.85
    },
    {
      "name": "Threat Region Access",
      "detected": false,
      "confidence": 0.90
    },
    {
      "name": "Unusual Device",
      "detected": false,
      "confidence": 0.50
    }
  ],
  "explanation": {
    "base_value": 0.0521,
    "total_prediction": 0.0521,
    "top_features": [                        # Top 3 factors
      {
        "feature": "login_hour",
        "value": 14.0,
        "shap_value": 0.0123,
        "contribution": "decreases_anomaly"
      },
      {
        "feature": "failed_attempts",
        "value": 2.0,
        "shap_value": -0.0045,
        "contribution": "decreases_anomaly"
      }
    ],
    "anomaly_reason": "Normal business hours + low failed attempts"
  }
}

EXAMPLE CURL:
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "login_hour": 14,
    "failed_attempts": 2,
    "device_type": 1,
    "location_code": 50,
    "login_frequency": 15,
    "latitude": 40.7128,
    "longitude": -74.0060
  }'

REAL-WORLD USE:
- Real-time login event analysis
- SIEM integration
- Active directory hook
- VPN access monitoring

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 2: /api/v1/bulk-predict
─────────────────────────────────
METHOD: POST
PURPOSE: Analyze risk for MULTIPLE logins in ONE request (batch processing)

WHAT IT DOES:
- Accepts array of login records
- Processes all in parallel
- Returns aggregated results
- Useful for batch analysis

INPUT (JSON body):
{
  "logins": [
    {
      "login_hour": 14,
      "failed_attempts": 2,
      "device_type": 1,
      "location_code": 50,
      "login_frequency": 15,
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    {
      "login_hour": 3,              # Suspicious: 3 AM
      "failed_attempts": 25,        # Suspicious: 25 attempts
      "device_type": 0,
      "location_code": 80,
      "login_frequency": 150,       # Suspicious: very high
      "latitude": 50.2,             # Threat region
      "longitude": 30.5             # Threat region
    }
  ]
}

OUTPUT (JSON response):
{
  "total": 2,                        # Total processed
  "anomalies": 1,                    # How many flagged
  "results": [
    {
      "login": {...login data...},
      "prediction": "NORMAL",
      "risk_score": 18.5,
      "risk_level": "LOW",
      "confidence": 87.3
    },
    {
      "login": {...login data...},
      "prediction": "ANOMALY",
      "risk_score": 85.2,
      "risk_level": "HIGH",
      "confidence": 92.5
    }
  ]
}

EXAMPLE CURL:
curl -X POST "http://localhost:8000/api/v1/bulk-predict" \
  -H "Content-Type: application/json" \
  -d '{"logins": [
    {"login_hour": 14, "failed_attempts": 2, "device_type": 1, "location_code": 50, "login_frequency": 15, "latitude": 40.7, "longitude": -74.0},
    {"login_hour": 3, "failed_attempts": 25, "device_type": 0, "location_code": 80, "login_frequency": 150, "latitude": 50.2, "longitude": 30.5}
  ]}'

REAL-WORLD USE:
- Daily/hourly batch analysis
- Historical log analysis
- Migration verification
- Incident investigation (analyze many logins)

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 3: /api/v1/threats
────────────────────────────
METHOD: GET
PURPOSE: Get recent detected anomalies/threats from database

WHAT IT DOES:
- Queries database for flagged logins
- Returns most recent anomalies
- Shows statistics

PARAMETERS:
?limit=50    # Optional: how many to return (1-500, default 50)

OUTPUT (JSON response):
{
  "total": 5,                        # How many threats found
  "critical_count": 1,               # CRITICAL severity count
  "high_count": 2,                   # HIGH severity count
  "threats": [
    {
      "id": 1,
      "login_hour": 3,
      "failed_attempts": 28,
      "device_type": 0,
      "location_code": 80,
      "login_frequency": 145,
      "latitude": 50.2,
      "longitude": 30.5,
      "created_at": "2026-02-09 14:32:15",
      "prediction": -1,              # -1 = anomaly, 1 = normal
      "decision_score": -0.0856,
      "risk_level": "CRITICAL",
      "pred_time": "2026-02-09 14:32:16"
    }
  ]
}

EXAMPLE CURL:
curl "http://localhost:8000/api/v1/threats?limit=10"

REAL-WORLD USE:
- Security dashboard
- SOC alert feed
- Incident management
- Threat intelligence export

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 4: /api/v1/statistics
───────────────────────────────
METHOD: GET
PURPOSE: Get system metrics and overall statistics

WHAT IT DOES:
- Returns dataset statistics
- Shows model status
- Provides summary metrics

PARAMETERS: None

OUTPUT (JSON response):
{
  "timestamp": "2026-02-09T14:35:22.123456",
  "statistics": {
    "total_logins": 1250,            # Total records analyzed
    "anomalies_detected": 127,       # Total anomalies found
    "alerts_sent": 45,               # Alerts dispatched
    "anomaly_rate": 10.16            # Percentage
  },
  "model_status": "ready",           # Model loaded?
  "explainer_status": "ready"        # SHAP available?
}

EXAMPLE CURL:
curl "http://localhost:8000/api/v1/statistics"

REAL-WORLD USE:
- System health monitoring
- Metrics collection (Prometheus/Datadog)
- Dashboard KPIs
- Alerting thresholds

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 5: /api/v1/feature-importance
───────────────────────────────────────
METHOD: GET
PURPOSE: Get global feature importance scores across ALL predictions

WHAT IT DOES:
- Calculates which features are most important
- Shows feature correlations with anomalies
- Uses SHAP values

PARAMETERS: None

OUTPUT (JSON response):
{
  "feature_importance": {
    "login_hour": 0.0847,            # SHAP importance score
    "failed_attempts": 0.1523,       # High importance
    "device_type": 0.0234,
    "location_code": 0.0512,
    "login_frequency": 0.1389,       # High importance
    "latitude": 0.0823,
    "longitude": 0.0762
  },
  "anomaly_correlations": {          # Correlation with anomalies
    "login_hour": -0.23,             # Night logins = anomalies
    "failed_attempts": 0.87,         # Strong correlation
    "device_type": 0.12,
    "location_code": 0.34,
    "login_frequency": 0.81,         # Strong correlation
    "latitude": 0.45,
    "longitude": 0.42
  },
  "features": [
    "login_hour",
    "failed_attempts",
    "device_type",
    "location_code",
    "login_frequency",
    "latitude",
    "longitude"
  ]
}

EXAMPLE CURL:
curl "http://localhost:8000/api/v1/feature-importance"

REAL-WORLD USE:
- Model interpretation
- Feature engineering
- Risk assessment tuning
- Business intelligence

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 6: /api/v1/anomaly-patterns
─────────────────────────────────────
METHOD: GET
PURPOSE: Analyze and report patterns in detected anomalies

WHAT IT DOES:
- Looks at all anomalies
- Identifies common patterns
- Shows frequency of each pattern

PARAMETERS: None

OUTPUT (JSON response):
{
  "patterns": {
    "most_common_anomaly_patterns": [
      ["failed_attempts", 45],       # 45 anomalies had high failures
      ["login_frequency", 38],       # 38 had high frequency
      ["login_hour", 32],            # 32 occurred at night
      ["latitude", 28],              # 28 from threat locations
      ["longitude", 28]
    ],
    "pattern_percentages": {
      "failed_attempts": 37.5,       # 37.5% of anomalies
      "login_frequency": 31.67,
      "login_hour": 26.67,
      "latitude": 23.33,
      "longitude": 23.33
    },
    "total_anomalies_analyzed": 120
  }
}

INTERPRETATION:
- Failed attempts: Most common anomaly indicator
- Login frequency: Second most common
- Shows which attack patterns are most prevalent

EXAMPLE CURL:
curl "http://localhost:8000/api/v1/anomaly-patterns"

REAL-WORLD USE:
- Threat landscape analysis
- Attack trend identification
- Security posture assessment
- Annual security reports

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 7: /api/v1/report
────────────────────────────
METHOD: GET
PURPOSE: Generate intelligence report for executive/security team

WHAT IT DOES:
- Creates summary report
- Shows findings and status
- Provides recommendations

PARAMETERS:
?days=7      # Optional: report period (1-90 days, default 7)

OUTPUT (JSON response):
{
  "report_date": "2026-02-09T14:35:22.123456",
  "period_days": 7,
  "summary": {
    "total_logins": 1250,
    "anomalies_detected": 127,
    "anomaly_rate_percent": 10.16,
    "alerts_sent": 45
  },
  "status": "Active monitoring",
  "recommendations": [
    "Monitor geographic anomalies",
    "Review credential stuffing attempts",
    "Increase MFA for night logins"
  ]
}

EXAMPLE CURL:
curl "http://localhost:8000/api/v1/report?days=30"

REAL-WORLD USE:
- Executive dashboards
- Security audits
- Compliance reports
- Board meetings

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 8: /api/v1/feedback
──────────────────────────────
METHOD: POST
PURPOSE: Submit feedback on predictions for model improvement

WHAT IT DOES:
- Records analyst feedback
- Labels predictions (correct/incorrect)
- Collects notes
- Stores for retraining

INPUT (Query parameters):
/api/v1/feedback?prediction_id=123&actual_label=true_positive&notes=Confirmed%20credential%20attack

PARAMETERS:
- prediction_id (required): Which prediction to label
- actual_label (required): One of:
  - true_positive (correctly flagged anomaly)
  - false_positive (incorrectly flagged)
  - true_negative (correctly marked normal)
  - false_negative (missed anomaly)
- notes (optional): Any additional context

OUTPUT (JSON response):
{
  "status": "feedback_received",
  "prediction_id": 123,
  "label": "true_positive",
  "timestamp": "2026-02-09T14:35:22.123456"
}

EXAMPLE CURL:
curl -X POST "http://localhost:8000/api/v1/feedback?prediction_id=1&actual_label=true_positive&notes=Confirmed%20attack"

REAL-WORLD USE:
- Model continuous improvement
- Analyst validation
- False positive reduction
- Automated retraining signals

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 9: /health
────────────────────
METHOD: GET
PURPOSE: Health check - is the API working?

WHAT IT DOES:
- Returns system status
- Confirms all components loaded
- Quick validation

PARAMETERS: None

OUTPUT (JSON response):
{
  "status": "healthy",
  "model_loaded": true,              # ML model ready?
  "database_connected": true,        # DB working?
  "timestamp": "2026-02-09T14:35:22.123456"
}

EXAMPLE CURL:
curl "http://localhost:8000/health"

REAL-WORLD USE:
- Monitoring alerts
- Kubernetes health checks
- Load balancer probes
- Service status pages

═════════════════════════════════════════════════════════════════════════════════

ENDPOINT 10: / (Root)
─────────────────────
METHOD: GET
PURPOSE: API documentation and endpoint listing

WHAT IT DOES:
- Shows all available endpoints
- Lists parameters
- Provides quick reference

PARAMETERS: None

OUTPUT (JSON response):
{
  "name": "AI Login Anomaly Detection API",
  "version": "1.0.0",
  "endpoints": {
    "predictions": "/api/v1/predict (POST)",
    "bulk_predictions": "/api/v1/bulk-predict (POST)",
    "active_threats": "/api/v1/threats (GET)",
    "statistics": "/api/v1/statistics (GET)",
    "feature_importance": "/api/v1/feature-importance (GET)",
    "anomaly_patterns": "/api/v1/anomaly-patterns (GET)",
    "reports": "/api/v1/report (GET)",
    "feedback": "/api/v1/feedback (POST)",
    "health": "/health (GET)"
  },
  "documentation": "/docs",
  "database": "SQLite (anomaly_detection.db)",
  "model": "Isolation Forest"
}

EXAMPLE CURL:
curl "http://localhost:8000/"

═════════════════════════════════════════════════════════════════════════════════

QUICK START WORKFLOW
════════════════════

1. CHECK HEALTH
   curl "http://localhost:8000/health"
   → Confirms system is ready

2. TEST SINGLE PREDICTION
   curl -X POST "http://localhost:8000/api/v1/predict" \
     -H "Content-Type: application/json" \
     -d '{...login data...}'
   → Analyze 1 login in real-time

3. GET RECENT THREATS
   curl "http://localhost:8000/api/v1/threats?limit=10"
   → See most recent anomalies

4. CHECK STATISTICS
   curl "http://localhost:8000/api/v1/statistics"
   → See overall metrics

5. ANALYZE PATTERNS
   curl "http://localhost:8000/api/v1/anomaly-patterns"
   → Understand common attack types

6. GENERATE REPORT
   curl "http://localhost:8000/api/v1/report?days=7"
   → Create summary for leadership

═════════════════════════════════════════════════════════════════════════════════

REAL-WORLD INTEGRATION EXAMPLES
════════════════════════════════

SPLUNK INTEGRATION:
```python
import requests
import json

def send_to_splunk(login_data):
    response = requests.post(
        'http://localhost:8000/api/v1/predict',
        json=login_data
    )
    
    prediction = response.json()
    
    # Send to Splunk
    requests.post(
        'https://splunk.company.com:8088/services/collector',
        json={
            'event': prediction,
            'sourcetype': 'ai_anomaly',
            'source': 'login_detector'
        }
    )
```

JIRA TICKET CREATION:
```python
response = requests.post(
    'http://localhost:8000/api/v1/predict',
    json=login_data
)

if response.json()['risk_level'] == 'CRITICAL':
    jira.create_issue(
        project='SEC',
        summary='Critical login anomaly',
        description=response.json()['explanation']['anomaly_reason'],
        issuetype='Security Issue'
    )
```

DATABASE EXPORT:
```python
response = requests.get('http://localhost:8000/api/v1/threats?limit=1000')
threats = response.json()['threats']

df = pd.DataFrame(threats)
df.to_csv('security_threats.csv', index=False)
```

═════════════════════════════════════════════════════════════════════════════════

FULL INTERACTIVE DOCUMENTATION
═══════════════════════════════

For complete interactive documentation with try-it-out features:
Visit: http://localhost:8000/docs

This provides:
- Full parameter documentation
- Live API testing interface
- Response examples
- Schema definitions

═════════════════════════════════════════════════════════════════════════════════
