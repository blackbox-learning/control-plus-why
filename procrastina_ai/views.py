"""
ProcrastinaAI Views - Page rendering and API endpoints

This module contains:
- Page views: Render HTML templates
- API views: Return JSON responses for frontend

All views are function-based and well-commented for beginners.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import Session, Disappearance, Report
from .services import (
    generate_prediction,
    generate_disappearance_response,
    generate_daily_report,
    generate_funny_reasons,
)


# ============================================================
# PAGE VIEWS - Render HTML Templates
# ============================================================

def index(request):
    """
    Landing page for ProcrastinaAI.
    Shows hero section with features and call-to-action.
    """
    return render(request, 'procrastina_ai/index.html')


def setup(request):
    """
    Setup page where users enter their mood, interests, and tasks.
    Renders the form template.
    """
    return render(request, 'procrastina_ai/setup.html')


def prediction(request):
    """
    Prediction page showing AI-generated procrastination journey.
    Displays timeline of how user will procrastinate.
    """
    return render(request, 'procrastina_ai/prediction.html')


def dashboard(request):
    """
    Dashboard page with stats, recent excuses, and AI responses.
    Shows user's procrastination metrics for today.
    """
    return render(request, 'procrastina_ai/dashboard.html')


def report(request):
    """
    Daily report page with analytics and achievements.
    Shows procrastination score and AI-generated summary.
    """
    return render(request, 'procrastina_ai/report.html')


def funny_reasons(request):
    """
    Page showing funny reasons/excuses to procrastinate.
    Displays AI-generated excuses for each task.
    """
    return render(request, 'procrastina_ai/funny_reasons.html')


def disappearance(request):
    """
    Modal popup page asking where user went during procrastination.
    Renders the disappearance form modal.
    """
    return render(request, 'procrastina_ai/disappearance.html')


# ============================================================
# API VIEWS - Return JSON Responses
# ============================================================

@require_http_methods(["POST"])
def api_create_session(request):
    """
    API endpoint: Create a new session
    
    POST /projects/procrastina-ai/api/create-session/
    
    Request body:
    {
        "mood": "sleepy",
        "interests": ["YouTube", "AI", "Gaming"],
        "tasks": ["Record Video", "Send Email", "Code Review"]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "sessionId": "uuid",
            "message": "Session created successfully"
        }
    }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        mood = data.get('mood')
        interests = data.get('interests', [])
        tasks = data.get('tasks', [])

        # Validate required fields
        if not mood or not interests or not tasks:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: mood, interests, tasks'
            }, status=400)

        # Create session in database
        session = Session.objects.create(
            mood=mood,
            interests=interests,
            tasks=tasks
        )

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'mood': mood,
                'interests': interests,
                'tasks': tasks,
                'message': 'Session created successfully'
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_generate_prediction(request):
    """
    API endpoint: Generate procrastination prediction
    
    POST /projects/procrastina-ai/api/generate-prediction/
    
    Request body:
    {
        "sessionId": "uuid",
        "mood": "sleepy",
        "interests": ["YouTube", "AI", "Gaming"],
        "tasks": ["Record Video", "Send Email"]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "prediction": ["Step 1...", "Step 2...", ...],
            "confidence": 94
        }
    }
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        mood = data.get('mood')
        interests = data.get('interests', [])
        tasks = data.get('tasks', [])

        # Get session from database
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)

        # Generate prediction using AI service
        result = generate_prediction(mood, interests, tasks)

        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate prediction'
            }, status=500)

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'prediction': result['data'],
                'confidence': result.get('confidence', 94)
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_save_disappearance(request):
    """
    API endpoint: Save where user disappeared and get AI response
    
    POST /projects/procrastina-ai/api/save-disappearance/
    
    Request body:
    {
        "sessionId": "uuid",
        "disappearanceType": "youtube",
        "customLocation": null,
        "mood": "sleepy",
        "interests": ["YouTube"]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "disappearanceId": "uuid",
            "aiResponse": "Witty response here..."
        }
    }
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        disappearance_type = data.get('disappearanceType')
        custom_location = data.get('customLocation')
        mood = data.get('mood')
        interests = data.get('interests', [])

        # Get session from database
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)

        # Generate AI response
        result = generate_disappearance_response(
            disappearance_type,
            custom_location,
            mood,
            interests
        )

        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate response'
            }, status=500)

        # Save disappearance to database
        disappearance = Disappearance.objects.create(
            session=session,
            disappearance_type=disappearance_type,
            custom_location=custom_location,
            ai_response=result['data']
        )

        return JsonResponse({
            'success': True,
            'data': {
                'disappearanceId': str(disappearance.id),
                'sessionId': str(session.id),
                'disappearanceType': disappearance_type,
                'aiResponse': result['data']
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_generate_report(request):
    """
    API endpoint: Generate daily procrastination report
    
    POST /projects/procrastina-ai/api/generate-report/
    
    Request body:
    {
        "sessionId": "uuid",
        "tasksPlanned": 4,
        "tasksCompleted": 1,
        "disappearances": 7,
        "commonExcuse": "Researching workflow"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "reportId": "uuid",
            "procrastinationScore": 87,
            "aiSummary": "Today's summary..."
        }
    }
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        tasks_planned = data.get('tasksPlanned', 0)
        tasks_completed = data.get('tasksCompleted', 0)
        disappearances = data.get('disappearances', 0)
        common_excuse = data.get('commonExcuse', 'Unknown excuse')

        # Get session from database
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)

        # Generate report using AI service
        result = generate_daily_report(
            tasks_planned,
            tasks_completed,
            disappearances,
            common_excuse
        )

        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate report'
            }, status=500)

        # Save report to database
        report = Report.objects.create(
            session=session,
            tasks_planned=tasks_planned,
            tasks_completed=tasks_completed,
            total_disappearances=disappearances,
            procrastination_score=result['score'],
            ai_summary=result['data']
        )

        return JsonResponse({
            'success': True,
            'data': {
                'reportId': str(report.id),
                'sessionId': str(session.id),
                'tasksPlanned': tasks_planned,
                'tasksCompleted': tasks_completed,
                'totalDisappearances': disappearances,
                'procrastinationScore': result['score'],
                'aiSummary': result['data'],
                'date': report.report_date.isoformat()
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_generate_funny_reasons(request):
    """
    API endpoint: Generate funny reasons to procrastinate on a task
    
    POST /projects/procrastina-ai/api/generate-funny-reasons/
    
    Request body:
    {
        "sessionId": "uuid",
        "taskName": "Record Video",
        "mood": "motivated"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "sessionId": "uuid",
            "taskName": "Record Video",
            "reasons": ["Reason 1...", "Reason 2...", ...]
        }
    }
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        task_name = data.get('taskName')
        mood = data.get('mood', 'unknown')

        # Get session from database
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)

        # Generate funny reasons using AI service
        result = generate_funny_reasons(task_name, mood)

        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate reasons'
            }, status=500)

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'taskName': task_name,
                'reasons': result['data']
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

