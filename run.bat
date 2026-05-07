@echo off
REM ScanPlus Startup Script for Windows

echo Starting ScanPlus Application...

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt

REM Start API server in new window
echo Starting API server on port 5000...
start "ScanPlus API" cmd /k "cd api && python api.py"

REM Wait a bit for API to start
timeout /t 3 /nobreak >nul

REM Start frontend server in new window
echo Starting frontend server on port 8000...
start "ScanPlus Frontend" cmd /k "cd frontend && ..\venv\Scripts\python app.py"

echo.
echo ✅ ScanPlus is running!
echo    - API: http://127.0.0.1:5000
echo    - Frontend: http://127.0.0.1:8000
echo.
echo Close the server windows to stop the application
