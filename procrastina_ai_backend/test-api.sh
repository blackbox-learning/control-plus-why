#!/bin/bash
# ProcrastinaAI Backend API Testing Script
# This script contains cURL examples for testing all API endpoints

API_BASE="http://localhost:5000/api"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ProcrastinaAI™ Backend API Testing Script                ║"
echo "║     How can I procrastinate more efficiently?                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Make sure the backend is running: npm start"
echo "Server should be at: http://localhost:5000"
echo ""

# Test 1: Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s http://localhost:5000/health | jq .
echo ""
echo ""

# Test 2: Create Session
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Create Session"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SESSION_RESPONSE=$(curl -s -X POST "$API_BASE/create-session" \
  -H "Content-Type: application/json" \
  -d '{
    "mood": "Sleepy",
    "interests": ["YouTube", "AI", "Gaming"],
    "tasks": ["Record Video", "Send Email", "Code Review"]
  }')
echo "$SESSION_RESPONSE" | jq .

# Extract session ID for use in subsequent tests
SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.data.sessionId // empty')
if [ -z "$SESSION_ID" ]; then
  echo "⚠️  Failed to extract session ID. Check if backend is running."
  exit 1
fi
echo "✅ Session ID: $SESSION_ID"
echo ""
echo ""

# Test 3: Generate Prediction
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Generate Prediction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_BASE/generate-prediction" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"mood\": \"Sleepy\",
    \"interests\": [\"YouTube\", \"AI\", \"Gaming\"],
    \"tasks\": [\"Record Video\", \"Send Email\", \"Code Review\"]
  }" | jq .
echo ""
echo ""

# Test 4: Save Disappearance (YouTube option)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Save Disappearance (YouTube)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_BASE/save-disappearance" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"disappearanceType\": \"youtube\",
    \"mood\": \"Sleepy\",
    \"interests\": [\"YouTube\", \"AI\", \"Gaming\"]
  }" | jq .
echo ""
echo ""

# Test 5: Save Disappearance (Custom option)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Save Disappearance (Custom Location)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_BASE/save-disappearance" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"disappearanceType\": \"other\",
    \"customLocation\": \"Playing Valorant for 3 hours\",
    \"mood\": \"Motivated\",
    \"interests\": [\"Gaming\"]
  }" | jq .
echo ""
echo ""

# Test 6: Generate Report
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: Generate Report"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_BASE/generate-report" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"tasksPlanned\": 4,
    \"tasksCompleted\": 1,
    \"disappearances\": 7,
    \"commonExcuse\": \"Researching optimal workflow setup\"
  }" | jq .
echo ""
echo ""

# Test 7: Generate Funny Reasons
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: Generate Funny Reasons"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_BASE/generate-funny-reasons" \
  -H "Content-Type: application/json" \
  -d "{
    \"sessionId\": \"$SESSION_ID\",
    \"taskName\": \"Record Video\",
    \"mood\": \"Motivated\"
  }" | jq .
echo ""
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    All Tests Completed!                      ║"
echo "║              Session ID used: $SESSION_ID  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
