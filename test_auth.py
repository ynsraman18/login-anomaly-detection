"""
Test script for authentication endpoints
"""
import requests
import json
from auth import AuthDatabase

# Initialize auth database
auth_db = AuthDatabase()

print("=" * 60)
print("AI LOGIN ANOMALY - AUTHENTICATION TEST")
print("=" * 60)

# Test 1: Check default admin user
print("\n1. Checking default admin user...")
admin_user = auth_db.get_user_by_username('admin')
if not admin_user:
    print("   Need to add get_user_by_username method - trying with user creation...")
else:
    print(f"   ✓ Admin user exists: {admin_user['username']} (role: {admin_user['role']})")

# Test 2: Authentication
print("\n2. Testing authentication...")
success, token = auth_db.authenticate('admin', 'admin123')
if success and token:
    print(f"   ✓ Authentication successful")
    print(f"   ✓ Token generated: {token[:50]}...")
else:
    print("   ✗ Authentication failed")

# Test 3: Token verification
print("\n3. Testing token verification...")
if success and token:
    valid, payload = auth_db.verify_token(token)
    if valid and payload:
        print(f"   ✓ Token verified")
        print(f"   ✓ User: {payload['username']}")
        print(f"   ✓ Role: {payload['role']}")
        user_id = payload['user_id']
    else:
        print("   ✗ Token verification failed")

# Test 4: Get user by ID
print("\n4. Getting user by ID...")
if success:
    admin_full = auth_db.get_user(user_id)
    if admin_full:
        print(f"   ✓ User retrieved: {admin_full['username']} ({admin_full['role']})")
    else:
        print("   ✗ Could not retrieve user")

# Test 5: Create test users with different roles
print("\n5. Creating test users...")
test_users = [
    ('analyst_user', 'analyst@example.com', 'password123', 'analyst'),
    ('viewer_user', 'viewer@example.com', 'password123', 'viewer'),
]

for username, email, password, role in test_users:
    success, msg = auth_db.create_user(username, email, password, role)
    if success:
        print(f"   ✓ Created {username} ({role})")
    else:
        print(f"   ℹ {username}: {msg}")

# Test 6: List all users
print("\n6. Listing all users...")
users = auth_db.list_users()
for user in users:
    print(f"   • {user['username']} ({user['role']}) - Active: {user['is_active']}")

# Test 7: Role permissions
print("\n7. Testing role permissions...")
from auth import RoleChecker
for role in ['admin', 'analyst', 'viewer']:
    perms = RoleChecker.get_permissions(role)
    print(f"   {role}: {', '.join(perms)}")

# Test 8: Invalid authentication
print("\n8. Testing invalid authentication...")
success, result = auth_db.authenticate('admin', 'wrongpassword')
print(f"   ✓ Invalid password rejected: {not success}")

success, result = auth_db.authenticate('nonexistent', 'password123')
print(f"   ✓ Invalid user rejected: {not success}")

print("\n" + "=" * 60)
print("AUTHENTICATION TESTS COMPLETE")
print("=" * 60)

# API Testing Instructions
print("\n📌 API TESTING INSTRUCTIONS:")
print("\n1. Start the API server:")
print("   python -m uvicorn api:app --reload --port 8000")

print("\n2. In another terminal, test endpoints:")
print("\n   a) Login:")
print("      curl -X POST http://localhost:8000/auth/login \\")
print("        -H 'Content-Type: application/json' \\")
print("        -d '{\"username\":\"admin\",\"password\":\"admin123\"}'")

print("\n   b) Get your profile (with token from login):")
print("      curl -X GET http://localhost:8000/auth/profile \\")
print("        -H 'Authorization: Bearer <YOUR_TOKEN>'")

print("\n   c) Make a prediction (requires analyst or admin role):")
print("      curl -X POST http://localhost:8000/api/v1/predict \\")
print("        -H 'Content-Type: application/json' \\")
print("        -H 'Authorization: Bearer <YOUR_TOKEN>' \\")
print("        -d '{\"login_hour\":14,\"failed_attempts\":0,\"device_type\":1,\"location_code\":1,\"login_frequency\":15,\"latitude\":40.7128,\"longitude\":-74.0060}'")

print("\n   d) View threats (requires analyst or admin role):")
print("      curl -X GET http://localhost:8000/api/v1/threats \\")
print("        -H 'Authorization: Bearer <YOUR_TOKEN>'")

print("\n   e) Generate report (requires admin role only):")
print("      curl -X GET 'http://localhost:8000/api/v1/report?days=7' \\")
print("        -H 'Authorization: Bearer <YOUR_TOKEN>'")

print("\n3. Dashboard authentication:")
print("   streamlit run app.py")
print("   Login with: admin / admin123")
