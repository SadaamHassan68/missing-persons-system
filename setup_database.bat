@echo off
echo Setting up Missing Persons Database...

REM Check if XAMPP MySQL is running
netstat -an | find "3306" > nul
if errorlevel 1 (
    echo MySQL is not running. Please start XAMPP MySQL service first.
    pause
    exit /b
)

REM Import the SQL file
echo Importing database schema...
"C:\xampp\mysql\bin\mysql" -u root < database_setup.sql

if errorlevel 1 (
    echo Error importing database schema.
    pause
    exit /b
)

echo Database setup completed successfully!
echo.
echo You can now run the Django migrations:
echo python manage.py migrate
echo.
pause 