@echo off
REM ============================================================
REM ProcrastinaAI Desktop Agent Launcher
REM ============================================================
REM Usage: launch_agent.bat [session_id]
REM
REM If session_id is not provided, the script will attempt to
REM read it from the most recent active session in the database.
REM ============================================================

setlocal

cd /d "%~dp0"

echo.
echo  ProcrastinaAI Desktop Agent Launcher
echo  =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not found in PATH.
    echo  Install Python or activate your virtual environment.
    pause
    exit /b 1
)

REM Check if session_id was provided
if "%~1"=="" (
    echo  No session_id provided.
    echo.
    echo  Usage:
    echo    launch_agent.bat YOUR_SESSION_ID
    echo.
    echo  Find your session ID:
    echo    1. Open ProcrastinaAI in your browser
    echo    2. Open DevTools (F12) ^> Console
    echo    3. Run: JSON.parse(localStorage.getItem('procrastina_ai_session')).sessionId
    echo.
    set /p SESSION_ID="  Enter session ID: "
) else (
    set SESSION_ID=%~1
)

if "!SESSION_ID!"=="" (
    echo  ERROR: No session ID provided.
    pause
    exit /b 1
)

echo  Starting agent for session: %SESSION_ID%
echo  Logs will be written to: logs\agent.log
echo.
echo  Press Ctrl+C to stop the agent.
echo.

python agent.py %SESSION_ID%

echo.
echo  Agent stopped.
pause
