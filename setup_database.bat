@echo off
echo Setting up Missing Persons System database...

REM Check if MySQL is installed
where mysql >nul 2>nul
if %errorlevel% neq 0 (
    echo MySQL is not installed or not in PATH
    echo Please install MySQL and try again
    pause
    exit /b 1
)

REM Prompt for MySQL root password
set /p MYSQL_PWD=Enter MySQL root password: 

REM Create database and tables
echo Creating database and tables...
mysql -u root -p%MYSQL_PWD% < database_setup.sql

if %errorlevel% neq 0 (
    echo Error setting up database
    pause
    exit /b 1
)

echo Database setup completed successfully!
echo.
echo Default admin credentials:
echo Email: admin@example.com
echo Password: admin123
echo.
echo Please change these credentials after first login
pause 