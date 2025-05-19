@echo off
echo Starting Missing Persons System...

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error creating virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements if needed
if not exist venv\Lib\site-packages\flask (
    echo Installing requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error installing requirements
        pause
        exit /b 1
    )
)

REM Create uploads directory if it doesn't exist
if not exist static\uploads mkdir static\uploads

REM Run Flask application
echo Starting Flask application...
python app.py

REM Deactivate virtual environment
call venv\Scripts\deactivate 