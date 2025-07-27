@echo off
REM Quick installation script for sqlBackup on Windows

echo Installing sqlBackup...

REM Check if Python 3 is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed or not in PATH
    exit /b 1
)

echo Using pip for installation...

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo Installation complete!
echo.
echo Next steps:
echo 1. Copy config.ini.default to config.ini
echo 2. Edit config.ini to match your environment
echo 3. Run: python sqlBackup
echo.
echo For development installation, run: pip install -e .
