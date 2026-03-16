# Quick Start: Authentication Setup

## 1. Install Dependencies
```bash
pip install pyjwt scikit-learn pandas numpy streamlit fastapi uvicorn requests joblib shap
```

## 2. Test Authentication System
```bash
python test_auth.py
```

You should see:
```
✓ Admin user exists: admin (role: admin)
✓ Authentication successful
✓ Token generated: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
✓ Token verified
✓ User: admin
✓ Role: admin
✓ Created analyst_user (analyst)
✓ Created viewer_user (viewer)
```

## 3. Start the API Server
```bash
python -m uvicorn api:app --reload --port 8000
```

You'll see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

## 4. Test API Authentication (in another terminal)

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

Response:
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "admin",
  "role": "admin"
}
```

### Make Prediction with Token
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -d '{
    "login_hour": 14,
    "failed_attempts": 0,
    "device_type": 1,
    "location_code": 1,
    "login_frequency": 15,
    "latitude": 40.7128,
    "longitude": -74.0060
  }'
```

## 5. Start the Dashboard
```bash
streamlit run app.py
```

Opens at: http://localhost:8501

Login with:
- Username: `admin`
- Password: `admin123`

## Test Users Created

| User | Password | Role | Can |
|------|----------|------|-----|
| admin | admin123 | Admin | Everything |
| analyst_user | password123 | Analyst | Predict, view, download |
| viewer_user | password123 | Viewer | View only |

## What's Protected

| Endpoint | Required Role | Examples |
|----------|---------------|----------|
| `/auth/login` | None | Get JWT token |
| `/auth/profile` | Any | View your info |
| `/api/v1/predict` | Analyst+ | Single prediction |
| `/api/v1/threats` | Analyst+ | View anomalies |
| `/api/v1/report` | Admin | Generate reports |
| `/api/v1/feedback` | Analyst+ | Submit feedback |
| `/health` | None | Health check |

## Next Steps

1. ✅ Tests passing
2. ✅ API running with authentication
3. ✅ Dashboard login working
4. 📝 Change default admin password in production
5. 📝 Update JWT secret key in production
6. 📝 Enable HTTPS for all API calls

## Docs

- See `AUTHENTICATION.md` for full documentation
- API docs at: http://localhost:8000/docs
- Dashboard at: http://localhost:8501

---

**Everything working? Great!** Your system is now production-ready with enterprise authentication. 🎉
