@echo off
echo Starting AI Login Anomaly Detection Project...

echo Activating virtual environment...
call .\venv\Scripts\activate.bat

echo Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt

echo Starting API Server in a new window...
start "AI Login Anomaly - API Server" cmd /k "python -m uvicorn api:app --reload --port 8000"

echo Starting Streamlit Dashboard in a new window...
start "AI Login Anomaly - Streamlit Dashboard" cmd /k "streamlit run app.py"

echo Project services have been started in separate windows!
echo API Documentation: http://localhost:8000/docs
echo Dashboard: http://localhost:8501
pause
