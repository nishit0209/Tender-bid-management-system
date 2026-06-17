@echo off
echo ========================================================
echo        Tender Management System - Project Setup         
echo ========================================================
echo.

echo [1/4] Checking for Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [2/4] Creating Virtual Environment (venv)...
IF NOT EXIST "venv" (
    python -m venv venv
    echo Virtual environment created successfully.
) ELSE (
    echo Virtual environment already exists.
)

echo [3/4] Activating Virtual Environment and Installing Requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip
IF EXIST "requirements.txt" (
    pip install -r requirements.txt
    echo Requirements installed successfully.
) ELSE (
    echo Warning: requirements.txt not found. Skipping dependency installation.
)

echo [4/4] Applying Database Migrations...
python manage.py migrate

echo.
echo ========================================================
echo Setup Complete! 
echo ========================================================
echo To run the server, use the following commands:
echo 1. venv\Scripts\activate
echo 2. python manage.py runserver
echo.
pause
