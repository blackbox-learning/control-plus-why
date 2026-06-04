@echo off
REM ProcrastinaAI Backend API Testing Script for Windows
REM Make sure you have curl installed (it comes with Windows 10+)

setlocal enabledelayedexpansion

set API_BASE=http://localhost:5000/api

echo.
echo ============================================================
echo        ProcrastinaAI Backend API Testing Script
echo        How can I procrastinate more efficiently?
echo ============================================================
echo.
echo Make sure the backend is running: npm start
echo Server should be at: http://localhost:5000
echo.

REM Test 1: Health Check
echo ============================================================
echo TEST 1: Health Check
echo ============================================================
curl -s http://localhost:5000/health
echo.
echo.

REM Test 2: Create Session
echo ============================================================
echo TEST 2: Create Session
echo ============================================================
for /f "delims=" %%A in ('curl -s -X POST "%API_BASE%/create-session" ^
  -H "Content-Type: application/json" ^
  -d "{\"mood\": \"Sleepy\", \"interests\": [\"YouTube\", \"AI\", \"Gaming\"], \"tasks\": [\"Record Video\", \"Send Email\", \"Code Review\"]}"') do set SESSION_RESPONSE=%%A
echo %SESSION_RESPONSE%
echo.
echo.

REM Test 3: Generate Prediction
echo ============================================================
echo TEST 3: Generate Prediction
echo ============================================================
curl -s -X POST "%API_BASE%/generate-prediction" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\": \"test-session-id\", \"mood\": \"Sleepy\", \"interests\": [\"YouTube\", \"AI\", \"Gaming\"], \"tasks\": [\"Record Video\", \"Send Email\", \"Code Review\"]}"
echo.
echo.

REM Test 4: Save Disappearance
echo ============================================================
echo TEST 4: Save Disappearance
echo ============================================================
curl -s -X POST "%API_BASE%/save-disappearance" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\": \"test-session-id\", \"disappearanceType\": \"youtube\", \"mood\": \"Sleepy\", \"interests\": [\"YouTube\", \"AI\", \"Gaming\"]}"
echo.
echo.

REM Test 5: Generate Report
echo ============================================================
echo TEST 5: Generate Report
echo ============================================================
curl -s -X POST "%API_BASE%/generate-report" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\": \"test-session-id\", \"tasksPlanned\": 4, \"tasksCompleted\": 1, \"disappearances\": 7, \"commonExcuse\": \"Researching optimal workflow setup\"}"
echo.
echo.

REM Test 6: Generate Funny Reasons
echo ============================================================
echo TEST 6: Generate Funny Reasons
echo ============================================================
curl -s -X POST "%API_BASE%/generate-funny-reasons" ^
  -H "Content-Type: application/json" ^
  -d "{\"sessionId\": \"test-session-id\", \"taskName\": \"Record Video\", \"mood\": \"Motivated\"}"
echo.
echo.

echo ============================================================
echo                    All Tests Completed!
echo ============================================================
echo.

pause
