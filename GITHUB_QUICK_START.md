# 5-Minute GitHub Setup

Quick reference to push your project to GitHub.

## Prerequisites

- GitHub account: [github.com](https://github.com)
- Git installed (Windows: [git-scm.com](https://git-scm.com))
- Your project directory ready

## Commands (Copy & Paste)

### 1. Configure Git (First time only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Initialize & Commit
```bash
cd C:\Users\ynsra\Documents\ai-login-anomaly
git init
git add .
git commit -m "Initial commit: AI Login Anomaly Detection with JWT Authentication"
```

### 3. Create Repo on GitHub
1. Go to [github.com/new](https://github.com/new)
2. **Name:** `ai-login-anomaly`
3. **Description:** `ML anomaly detection with JWT auth`
4. **Visibility:** Public or Private
5. Click **Create repository**
6. Copy the HTTPS URL shown

### 4. Connect & Push
```bash
# Replace USERNAME with your GitHub username
git remote add origin https://github.com/USERNAME/ai-login-anomaly.git
git branch -M main
git push -u origin main
```

### 5. Verify
- Visit `https://github.com/USERNAME/ai-login-anomaly`
- Should see all files ✅

## What Gets Pushed

✅ Pushed to GitHub:
- Python source code (`.py` files)
- Documentation (`.md` files)
- Requirements (`requirements.txt`)
- License & README
- Configuration examples (`.env.example`)

❌ NOT pushed (protected by `.gitignore`):
- Databases (`*.db`)
- Model files (`*.pkl`)
- Secrets (`.env`)
- Virtual environment (`venv/`)

## For Railway Deployment

After pushing to GitHub:

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. "New Project" → Select `ai-login-anomaly`
4. Railway auto-deploys
5. Set environment variables in Railway dashboard
6. Done!

## Future Updates

```bash
# Make changes...

git add .
git commit -m "Description of changes"
git push
```

That's it! See [GITHUB_SETUP.md](GITHUB_SETUP.md) for detailed guide.
