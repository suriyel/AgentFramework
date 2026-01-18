@echo off
echo Starting Agent Workstation Backend...
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting FastAPI server...
python -m backend.api.main

pause
