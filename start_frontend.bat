@echo off
echo Starting Agent Workstation Frontend...
echo.

cd frontend

echo Installing dependencies (if needed)...
call npm install

echo.
echo Starting development server...
call npm run dev

pause
