@echo off
echo Starting Bot Marketplace Services...
echo.

REM Start API Server
start "API Server" cmd /k "python main.py"
timeout /t 3 /nobreak > nul

REM Start Celery Worker  
start "Celery Worker" cmd /k "celery -A tasks worker --loglevel=info --concurrency=4"
timeout /t 3 /nobreak > nul

REM Start Celery Beat
start "Celery Beat" cmd /k "celery -A tasks beat --loglevel=info"
timeout /t 3 /nobreak > nul

echo.
echo All services started!
echo.
echo Services running:
echo - API Server: http://localhost:8000
echo - Celery Worker: Bot execution
echo - Celery Beat: Task scheduler
echo.
echo Press any key to continue...
pause > nul 