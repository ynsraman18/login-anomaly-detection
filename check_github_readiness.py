#!/usr/bin/env python3
"""
GitHub Repository Readiness Checker
Verifies all files are ready for GitHub push
"""

import os
import sys

def check_github_readiness():
    """Check if project is ready for GitHub"""
    
    print("=" * 70)
    print("📦 GITHUB READINESS CHECKER")
    print("=" * 70)
    
    checks = {
        "Critical Files": {
            ".gitignore": True,
            ".env.example": True,
            "requirements.txt": True,
            "LICENSE": True,
            "README.md": True,
        },
        "Python Source Code": {
            "app.py": True,
            "api.py": True,
            "auth.py": True,
            "database.py": True,
            "train_model.py": True,
        },
        "Documentation": {
            "GITHUB_SETUP.md": True,
            "GITHUB_QUICK_START.md": True,
            "AUTHENTICATION.md": True,
            "DEPLOYMENT.md": True,
            "QUICKSTART.md": True,
        },
        "Data & Models": {
            "model.pkl": True,
            "login_data.csv": True,
        },
        "Tests": {
            "test_auth.py": True,
            "verify_system.py": True,
        }
    }
    
    total = 0
    passed = 0
    
    for category, files in checks.items():
        print(f"\n📋 {category}:")
        for filename, _ in files.items():
            exists = os.path.exists(filename)
            status = "✅" if exists else "❌"
            print(f"  {status} {filename}")
            total += 1
            if exists:
                passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 SCORE: {passed}/{total} files ready ({100*passed//total}%)")
    print("=" * 70)
    
    # Security checks
    print("\n🔒 SECURITY CHECKS:")
    
    # Check .gitignore has database exclusions
    with open(".gitignore", "r") as f:
        gitignore = f.read()
    
    security_items = [
        ("*.db in .gitignore", "*.db" in gitignore),
        (".env in .gitignore", ".env" in gitignore),
        ("venv/ in .gitignore", "venv/" in gitignore),
        ("__pycache__/ in .gitignore", "__pycache__/" in gitignore),
    ]
    
    for check, result in security_items:
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    # Check .env.example exists
    env_example_exists = os.path.exists(".env.example")
    print(f"  {'✅' if env_example_exists else '❌'} .env.example exists (template for secrets)")
    
    # Check .env does NOT exist (should never be in repo)
    env_exists = os.path.exists(".env")
    print(f"  {'✅' if not env_exists else '❌'} .env does NOT exist (good for security)")
    
    # Check databases do NOT exist (should be generated at runtime)
    auth_db = os.path.exists("auth.db")
    anomaly_db = os.path.exists("anomaly_detection.db")
    print(f"  {'⚠️' if auth_db else '✅'} auth.db exists (will be generated at runtime)")
    print(f"  {'⚠️' if anomaly_db else '✅'} anomaly_detection.db exists (will be generated at runtime)")
    
    print("\n" + "=" * 70)
    print("✅ READY FOR GITHUB" if passed >= 18 else "❌ NOT READY - Fix missing files")
    print("=" * 70)
    
    print("\n📝 NEXT STEPS:")
    print("""
1. Read GITHUB_QUICK_START.md for 5-minute setup
2. Configure Git:
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"

3. Initialize repo:
   git init
   git add .
   git commit -m "Initial commit: AI Login Anomaly Detection with JWT Authentication"

4. Create repo on GitHub at https://github.com/new
   Name: ai-login-anomaly
   Description: ML anomaly detection with JWT auth
   Visibility: Public or Private

5. Push to GitHub:
   git remote add origin https://github.com/USERNAME/ai-login-anomaly.git
   git branch -M main
   git push -u origin main

6. Deploy to Railway:
   Go to https://railway.app
   Sign in with GitHub
   Select ai-login-anomaly repo
   Railway auto-deploys!

📚 DOCUMENTATION:
- GITHUB_SETUP.md - Detailed setup guide
- GITHUB_QUICK_START.md - Quick reference
- DEPLOYMENT.md - Railway deployment
- AUTHENTICATION.md - Auth system guide
- README.md - Full documentation
""")
    
    return 0 if passed >= 18 else 1

if __name__ == "__main__":
    sys.exit(check_github_readiness())
