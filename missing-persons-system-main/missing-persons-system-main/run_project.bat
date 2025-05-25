@echo off
echo Starting Missing Persons Project Setup...

REM Check if XAMPP MySQL is running
netstat -an | find "3306" > nul
if errorlevel 1 (
    echo MySQL is not running. Please start XAMPP MySQL service first.
    pause
    exit /b
)

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH. Please install Python first.
    pause
    exit /b
)

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install requirements if not already installed
echo Installing requirements...
pip install -r requirements.txt

REM Run database setup
echo Setting up database...
call setup_database.bat

REM Run Django migrations
echo Running Django migrations...
python manage.py migrate

REM Check if superuser exists, if not create one
echo Checking for superuser...
python manage.py shell -c "from django.contrib.auth.models import User; print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser found')" | find "No superuser found" > nul
if not errorlevel 1 (
    echo Creating superuser...
    python manage.py createsuperuser
)

REM Start the development server
echo Starting development server...
echo.
echo The application will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver

pause 