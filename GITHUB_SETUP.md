# GitHub Setup Instructions

Complete guide to push your AI Login Anomaly Detection system to GitHub.

## Step 1: Configure Git (First Time Only)

```bash
# Set your Git identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 2: Initialize Local Repository

```bash
# Navigate to project directory
cd C:\Users\ynsra\Documents\ai-login-anomaly

# Initialize Git
git init

# Check what will be staged
git status

# Add all files (respecting .gitignore)
git add .

# Verify files to be committed
git status

# Create first commit
git commit -m "Initial commit: AI Login Anomaly Detection with JWT Authentication"
```

## Step 3: Create GitHub Repository

1. Go to **[github.com](https://github.com)**
2. Click **"New"** or go to **"Your repositories"** → **"New"**
3. Fill in:
   - **Repository name:** `ai-login-anomaly`
   - **Description:** `Enterprise-grade ML anomaly detection with JWT authentication and role-based access control`
   - **Visibility:** Public (for portfolio) or Private (for security)
4. **DO NOT** initialize with:
   - README (you already have one)
   - .gitignore (you already have one)
   - License (you already have one)
5. Click **"Create repository"**

## Step 4: Connect Local to Remote

After creating the repository, GitHub shows commands. Copy the HTTPS URL and run:

```bash
# Add remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/ai-login-anomaly.git

# Rename branch to main (GitHub default)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 5: Verify on GitHub

1. Go to your repository on GitHub
2. Should see all files including:
   - ✅ README.md
   - ✅ .gitignore
   - ✅ LICENSE
   - ✅ requirements.txt
   - ✅ All Python source files
   - ✅ Documentation files
3. Should **NOT** see:
   - ❌ `*.db` (databases)
   - ❌ `*.pkl` (models)
   - ❌ `.env` (secrets)
   - ❌ `venv/` (virtual environment)
   - ❌ `__pycache__/`

## Step 6: Future Commits

After setup, use these commands:

```bash
# Make changes to your code

# Stage changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push
```

## Troubleshooting

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/USERNAME/ai-login-anomaly.git
```

### "Permission denied (publickey)"
You need SSH keys. Use HTTPS instead or:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to ssh-agent and GitHub settings
```

### ".gitignore not working"
```bash
# Remove cached files
git rm -r --cached .
git add .
git commit -m "Remove ignored files"
git push
```

## Files NOT Committed (Protected)

These files are in `.gitignore` and won't be pushed:

| File | Reason |
|------|--------|
| `auth.db` | Contains user passwords |
| `anomaly_detection.db` | Contains sensitive predictions |
| `model.pkl` | Large model file (~1.5MB) |
| `.env` | Contains secrets (JWT key, API keys) |
| `venv/` | Virtual environment (platform-specific) |
| `__pycache__/` | Python cache files |
| `.pytest_cache/` | Test cache |
| `*.log` | Log files |

## After Pushing to GitHub

### Set Up for Deployment

1. **Railway Deployment:**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `ai-login-anomaly`
   - Railway auto-detects Python and installs dependencies

2. **Environment Variables on Railway:**
   - Add `JWT_SECRET_KEY` (generate new value!)
   - Add `SLACK_WEBHOOK_URL` (if using alerts)
   - Add `SMTP_*` variables (if using email)

3. **Set Start Commands:**
   - Railway auto-detects Procfile (if present)
   - Or manually set: `python -m uvicorn api:app --host 0.0.0.0 --port $PORT`

### GitHub Actions (Optional CI/CD)

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python test_auth.py
```

## GitHub Best Practices

✅ **DO:**
- Write clear commit messages
- Commit frequently with logical changes
- Use branches for features: `git checkout -b feature/name`
- Keep `.env` in `.gitignore` always
- Add large files to `.gitignore`
- Document setup in README
- Update README with deployment status

❌ **DON'T:**
- Commit `.env` file
- Commit `*.db` or `*.pkl` files
- Commit virtual environments
- Make huge commits mixing many changes
- Commit API keys or passwords
- Ignore `.gitignore` with force push

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] `*.db` files are in `.gitignore`
- [ ] Repository is Private (if containing sensitive data)
- [ ] No API keys in code
- [ ] `.env.example` exists showing required variables
- [ ] GitHub is set to require HTTPS
- [ ] No secrets in commit history

## Repository Statistics

After pushing, your GitHub repo will show:

```
Language: Python
Commits: 1 (initial)
Stars: 0
Forks: 0
Issues: 0
Pull Requests: 0
Code: 3,500+ lines
```

## Next Steps

1. ✅ Push to GitHub
2. 🔄 Deploy to Railway (see DEPLOYMENT.md)
3. 📊 Monitor on Railway dashboard
4. 🔐 Configure secrets in Railway
5. 🚀 Access live system
6. 📝 Update README with live URL

## Support

- GitHub Docs: [docs.github.com](https://docs.github.com)
- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Git Help: `git --help` or `git COMMAND --help`

---

**Ready to push?** Run the commands in Step 2 and Step 4!
