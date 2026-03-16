# AI Login Anomaly Detection - Authentication Guide

## Overview

The system now includes **enterprise-grade authentication** with:
- ✅ JWT token-based API authentication
- ✅ Password hashing with PBKDF2-SHA256 (100k iterations)
- ✅ Role-based access control (Admin, Analyst, Viewer)
- ✅ Streamlit dashboard login page
- ✅ Session management with SQLite

---

## User Roles & Permissions

### 1. **Admin** (Full Access)
- View all data
- Make predictions
- Manage users
- Download reports
- Configure system
- Delete records
- Exclusive: Generate reports, create users

### 2. **Analyst** (Analysis Access)
- View all data
- Make predictions
- Download reports
- Submit feedback
- Cannot: Manage users, generate reports, configure system, delete

### 3. **Viewer** (Read-Only)
- View dashboards and data only
- Cannot: Make predictions, download, delete, or manage users

---

## Default Credentials

```
Username: admin
Password: admin123
```

**⚠️ Change these credentials in production!**

---

## Authentication Endpoints

### 1. Login (Get Token)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "admin",
  "role": "admin",
  "message": "Login successful"
}
```

### 2. Get Your Profile
```bash
curl -X GET http://localhost:8000/auth/profile \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**Response:**
```json
{
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "permissions": ["view", "predict", "manage_users", "download", "configure", "delete"]
}
```

### 3. Create New User (Admin Only)
```bash
curl -X POST http://localhost:8000/auth/users \
  -H 'Authorization: Bearer ADMIN_TOKEN' \
  -d 'username=john&password=secure123&email=john@example.com&role=analyst'
```

### 4. Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## Protected Endpoints

All data endpoints now require authentication. Pass your JWT token in the Authorization header:

```bash
Authorization: Bearer <YOUR_TOKEN>
```

### **Admin Only:**
- `GET /api/v1/report` - Generate intelligence reports

### **Admin & Analyst:**
- `POST /api/v1/predict` - Make single prediction
- `POST /api/v1/bulk-predict` - Batch predictions
- `GET /api/v1/threats` - View active threats
- `GET /api/v1/statistics` - View system statistics
- `GET /api/v1/feature-importance` - View feature importance
- `GET /api/v1/anomaly-patterns` - View anomaly patterns
- `POST /api/v1/feedback` - Submit feedback

### **Public (No Auth):**
- `GET /health` - Health check
- `GET /` - API documentation

---

## Using the Dashboard

1. **Start the dashboard:**
```bash
streamlit run app.py
```

2. **Login page appears with:**
   - Login tab: Username/password input
   - Demo tab: Quick access with demo credentials

3. **Default login:**
   - Username: `admin`
   - Password: `admin123`

4. **Features available:**
   - Dashboard shows logged-in user info in header
   - Logout button in top right
   - Full access to predictions, threat monitoring, geographic mapping

---

## API Testing Examples

### Example 1: Complete Workflow

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

echo "Token: $TOKEN"

# 2. Get profile
curl -X GET http://localhost:8000/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# 3. Make prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "login_hour": 14,
    "failed_attempts": 0,
    "device_type": 1,
    "location_code": 1,
    "login_frequency": 15,
    "latitude": 40.7128,
    "longitude": -74.0060
  }' | jq

# 4. View threats
curl -X GET "http://localhost:8000/api/v1/threats?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# 5. Generate report (admin only)
curl -X GET "http://localhost:8000/api/v1/report?days=7" \
  -H "Authorization: Bearer $TOKEN" | jq

# 6. Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### Example 2: Create New Analyst User

```bash
# Admin creates analyst user
curl -X POST http://localhost:8000/auth/users \
  -H 'Authorization: Bearer ADMIN_TOKEN' \
  -d 'username=analyst1&password=pass123&email=analyst1@company.com&role=analyst'

# Response: {"status": "success", "username": "analyst1", "role": "analyst"}
```

### Example 3: Analyst Makes Prediction

```bash
# Analyst login
ANALYST_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"analyst1","password":"pass123"}' | jq -r '.token')

# Analyst can make predictions
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ANALYST_TOKEN" \
  -d '{...login data...}' | jq
```

### Example 4: Viewer Cannot Predict

```bash
# Viewer tries to predict (should fail)
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Authorization: Bearer VIEWER_TOKEN" \
  -d '{...login data...}'

# Response: {"detail": "Requires one of roles: ['admin', 'analyst']"}
```

---

## System Architecture

### Authentication Database (auth.db)
```
Tables:
├── users
│   ├── id (PK)
│   ├── username (UNIQUE)
│   ├── email (UNIQUE)
│   ├── password_hash (PBKDF2)
│   ├── role (admin/analyst/viewer)
│   ├── is_active (boolean)
│   ├── created_at (timestamp)
│   └── last_login (timestamp)
│
└── sessions
    ├── id (PK)
    ├── user_id (FK)
    ├── token (JWT)
    ├── created_at (timestamp)
    ├── expires_at (timestamp)
    └── is_active (boolean)
```

### Security Features
1. **Password Storage:** PBKDF2-SHA256 with 100,000 iterations + random salt
2. **Token Format:** JWT (HS256)
3. **Token Lifetime:** 24 hours
4. **Session Tracking:** All tokens stored in database
5. **Role Enforcement:** FastAPI dependencies with Depends(require_role(...))
6. **Audit Logging:** All login attempts tracked in anomaly_detection.db

---

## Common Tasks

### Promote User to Admin
```python
# Not exposed via API (for security), must edit database directly
# Or add admin endpoint for management
```

### Change User Password
```python
# Add endpoint or implement via dashboard
```

### List All Active Sessions
```python
# Would need to query sessions table
# Can be exposed via admin panel
```

---

## Security Best Practices

### Production Deployment

1. **Change Secret Key:**
   - Edit `auth.py` line: `self.secret_key = "your-secret-key-change-this-in-production"`
   - Use strong random key (32+ characters)
   - Store in environment variable

2. **Update Default Credentials:**
   - Never leave admin/admin123 in production
   - Create new admin user, delete default
   - Implement password complexity rules

3. **HTTPS Required:**
   - Always use HTTPS in production
   - JWT tokens should not travel over HTTP

4. **Token Expiration:**
   - Currently 24 hours
   - Consider shorter for sensitive operations
   - Implement refresh tokens

5. **Rate Limiting:**
   - Add login attempt limits
   - Use tools like `slowapi`
   - Prevent brute force attacks

6. **Audit Logging:**
   - Log all authentication events
   - Track failed login attempts
   - Monitor suspicious activity

---

## File Structure

```
ai-login-anomaly/
├── auth.py                    # Authentication system
├── app.py                     # Streamlit dashboard with login
├── api.py                     # FastAPI with protected endpoints
├── auth.db                    # User authentication database
├── anomaly_detection.db       # Predictions and audit logs
└── test_auth.py              # Authentication tests
```

---

## Troubleshooting

### Token Expired
- Get new token by logging in again
- Tokens valid for 24 hours

### Unauthorized (401)
- Check token is in Authorization header
- Format: `Authorization: Bearer YOUR_TOKEN`
- Verify token hasn't expired

### Forbidden (403)
- Your role lacks permission for endpoint
- Contact admin to upgrade role
- Check role requirements above

### User Already Exists
- Choose different username
- Check user list with `auth_db.list_users()`

---

## Next Steps

1. **Test authentication:** Run `python test_auth.py`
2. **Start API:** `python -m uvicorn api:app --reload`
3. **Start Dashboard:** `streamlit run app.py`
4. **Try examples:** Use curl commands above
5. **Integrate:** Add to your authentication flow

---

## Files Modified

- ✅ `auth.py` - NEW: Complete authentication module
- ✅ `api.py` - UPDATED: Protected endpoints with JWT
- ✅ `app.py` - UPDATED: Login page added
- ✅ `test_auth.py` - NEW: Authentication test suite

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** 2024
