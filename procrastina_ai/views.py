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
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Session, Disappearance, Report
from .services import (
    generate_prediction,
    generate_disappearance_response,
    generate_daily_report,
    generate_funny_reasons,
    generate_idle_return_options,
)
from . import activity_services
from . import desktop_integration


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


# ============================================================
# API VIEWS - Return JSON Responses
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_create_session(request):
    """
    API endpoint: Create a new session

    POST /projects/procrastina-ai/api/create-session/
    """
    try:
        data = json.loads(request.body)
        mood = data.get('mood')
        interests = data.get('interests', [])
        tasks = data.get('tasks', [])

        if not mood or not interests or not tasks:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: mood, interests, tasks'
            }, status=400)

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
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_prediction(request):
    """
    API endpoint: Generate procrastination prediction

    POST /projects/procrastina-ai/api/generate-prediction/
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        mood = data.get('mood')
        interests = data.get('interests', [])
        tasks = data.get('tasks', [])

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        result = generate_prediction(mood, interests, tasks)

        if not result['success']:
            return JsonResponse({'success': False, 'error': 'Failed to generate prediction'}, status=500)

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'prediction': result['data'],
                'confidence': result.get('confidence', 94)
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_save_disappearance(request):
    """
    API endpoint: Save where user disappeared and get AI response

    POST /projects/procrastina-ai/api/save-disappearance/
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        disappearance_type = data.get('disappearanceType')
        custom_location = data.get('customLocation')
        mood = data.get('mood')
        interests = data.get('interests', [])

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        result = generate_disappearance_response(
            disappearance_type, custom_location, mood, interests
        )

        if not result['success']:
            return JsonResponse({'success': False, 'error': 'Failed to generate response'}, status=500)

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
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_report(request):
    """
    API endpoint: Generate daily procrastination report

    POST /projects/procrastina-ai/api/generate-report/

    DUAL DATA SOURCE SUPPORT:
    - If desktop activity data exists (ActivitySession), uses enhanced report
    - Otherwise falls back to manual-only report (current behavior)
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        tasks_planned = data.get('tasksPlanned', 0)
        tasks_completed = data.get('tasksCompleted', 0)
        disappearances = data.get('disappearances', 0)
        common_excuse = data.get('commonExcuse', 'Unknown excuse')

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        # Check if activity data exists for enhanced reporting
        has_activity = session.activity_sessions.exists()

        if has_activity:
            # Use enhanced report with activity data
            enhanced = activity_services.generate_enhanced_report(session_id)
            if enhanced['success']:
                # Use enhanced score and summary
                score = enhanced['score']
                ai_summary = enhanced['data']
            else:
                # Fallback to manual
                result = generate_daily_report(
                    tasks_planned, tasks_completed, disappearances, common_excuse
                )
                score = result.get('score', 50)
                ai_summary = result.get('data', 'Report generation failed.')
        else:
            # Manual-only report (current behavior)
            result = generate_daily_report(
                tasks_planned, tasks_completed, disappearances, common_excuse
            )
            if not result['success']:
                return JsonResponse({'success': False, 'error': 'Failed to generate report'}, status=500)
            score = result['score']
            ai_summary = result['data']

        report_obj = Report.objects.create(
            session=session,
            tasks_planned=tasks_planned,
            tasks_completed=tasks_completed,
            total_disappearances=disappearances,
            procrastination_score=score,
            ai_summary=ai_summary
        )

        return JsonResponse({
            'success': True,
            'data': {
                'reportId': str(report_obj.id),
                'sessionId': str(session.id),
                'tasksPlanned': tasks_planned,
                'tasksCompleted': tasks_completed,
                'totalDisappearances': disappearances,
                'procrastinationScore': score,
                'aiSummary': ai_summary,
                'date': report_obj.report_date.isoformat(),
                'hasActivityData': has_activity,
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_funny_reasons(request):
    """
    API endpoint: Generate funny reasons to procrastinate on a task

    POST /projects/procrastina-ai/api/generate-funny-reasons/
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        task_name = data.get('taskName')
        mood = data.get('mood', 'unknown')

        # Session is optional for funny reasons (allow without session)
        session = None
        if session_id:
            try:
                session = Session.objects.get(id=session_id)
            except Session.DoesNotExist:
                pass

        result = generate_funny_reasons(task_name, mood)

        if not result['success']:
            return JsonResponse({'success': False, 'error': 'Failed to generate reasons'}, status=500)

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id) if session else None,
                'taskName': task_name,
                'reasons': result['data']
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================
# GET API ENDPOINTS — Retrieve session data for frontend
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_end_session(request):
    """
    API endpoint: End active session ('Stop My Day')

    POST /projects/procrastina-ai/api/end-session/
    Marks the session as inactive and stores final activity data.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        active_seconds = data.get('activeSeconds', 0)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        session.is_active = False
        session.ended_at = timezone.now()
        # Use final heartbeat value if provided, otherwise keep last saved value
        if active_seconds > 0:
            session.active_seconds = active_seconds
        # Mark data sufficient if we have at least 30 seconds of tracked activity
        session.activity_data_sufficient = session.active_seconds >= 30
        session.save()

        # Auto-end any active agent ActivitySession linked to this session
        active_agent = session.activity_sessions.filter(is_active=True).first()
        if active_agent:
            desktop_integration.process_end_session({
                'activitySessionId': str(active_agent.id)
            })

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'activeSeconds': session.active_seconds,
                'message': 'Session ended. Time to face the report.'
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_heartbeat(request):
    """
    API endpoint: Receive activity heartbeat from client

    POST /projects/procrastina-ai/api/activity-heartbeat/
    Client sends accumulated active seconds periodically.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        active_seconds = data.get('activeSeconds', 0)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        if session.is_active:
            session.active_seconds = active_seconds
            session.save(update_fields=['active_seconds', 'updated_at'])

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'activeSeconds': session.active_seconds,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_get_session_data(request):
    """
    GET /projects/procrastina-ai/api/session-data/?sessionId=xxx

    Returns session data + disappearances for the given session.
    """
    session_id = request.GET.get('sessionId')
    if not session_id:
        return JsonResponse({'success': False, 'error': 'sessionId required'}, status=400)

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

    disappearances = session.disappearances.all()
    reports = session.reports.all()

    # Build distraction breakdown from disappearances
    type_counts = {}
    for d in disappearances:
        t = d.disappearance_type
        type_counts[t] = type_counts.get(t, 0) + 1

    # Most common excuse
    common_excuse = max(type_counts, key=type_counts.get) if type_counts else 'Unknown'

    # Calculate session length
    ended = session.ended_at or timezone.now()
    session_length_seconds = (ended - session.created_at).total_seconds()

    # Build response data
    response_data = {
        'sessionId': str(session.id),
        'mood': session.mood,
        'interests': session.interests,
        'tasks': session.tasks,
        'isActive': session.is_active,
        'createdAt': session.created_at.isoformat(),
        'endedAt': session.ended_at.isoformat() if session.ended_at else None,
        'activeSeconds': session.active_seconds,
        'sessionLengthSeconds': session_length_seconds,
        'activityDataSufficient': session.activity_data_sufficient,
        'disappearances': [
            {
                'id': str(d.id),
                'type': d.disappearance_type,
                'customLocation': d.custom_location,
                'aiResponse': d.ai_response,
                'createdAt': d.created_at.isoformat(),
            }
            for d in disappearances
        ],
        'disappearanceCount': disappearances.count(),
        'reports': [
            {
                'id': str(r.id),
                'tasksPlanned': r.tasks_planned,
                'tasksCompleted': r.tasks_completed,
                'totalDisappearances': r.total_disappearances,
                'procrastinationScore': r.procrastination_score,
                'aiSummary': r.ai_summary,
                'date': r.report_date.isoformat(),
            }
            for r in reports
        ],
        'distractionBreakdown': type_counts,
        'commonExcuse': common_excuse,
    }

    # Include activity summary data if available (from desktop agent)
    has_activity = session.activity_sessions.exists()
    response_data['hasActivityData'] = has_activity

    if has_activity:
        # Get agent status and activity summary
        agent_status = desktop_integration.get_agent_status(session_id)
        response_data['agentStatus'] = agent_status

        # Get lightweight activity summary (top apps, categories)
        analytics = activity_services.get_session_analytics(session_id)
        if analytics['success']:
            a = analytics['data']
            response_data['activitySummary'] = {
                'topApps': a['topApps'][:5],
                'topWebsites': a['topWebsites'][:5],
                'categoryBreakdown': a['categoryBreakdown'],
                'activeSeconds': a['activeSeconds'],
                'idleSeconds': a['idleSeconds'],
                'focusChanges': a['focusChanges'],
                'currentApp': a['currentApp'],
                'agentConnected': a['agentConnected'],
            }

    return JsonResponse({
        'success': True,
        'data': response_data,
    })


# ============================================================
# IDLE RETURN + SESSION RECOVERY + AGENT MANAGEMENT
# ============================================================

@require_http_methods(["GET"])
def api_idle_return_options(request):
    """
    GET /projects/procrastina-ai/api/idle-return-options/?sessionId=xxx

    Returns contextual distraction options for the idle-return popup.
    Uses mood, interests, last active app, and previous distraction history.
    """
    session_id = request.GET.get('sessionId')
    if not session_id:
        return JsonResponse({'success': False, 'error': 'sessionId required'}, status=400)

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

    # Gather context
    mood = session.mood or 'lazy'
    interests = session.interests or []
    history = [d.disappearance_type for d in session.disappearances.all()[:5]]

    # Last active app from agent (if connected)
    last_app = ''
    active_agent = session.activity_sessions.filter(is_active=True).first()
    if active_agent:
        last_app = active_agent.last_active_app

    options = generate_idle_return_options(mood, interests, last_app, history)

    return JsonResponse({
        'success': True,
        'data': {
            'options': options,
            'idleDurationSeconds': 0,  # frontend supplies this from agentStatus
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_save_return_reason(request):
    """
    POST /projects/procrastina-ai/api/save-return-reason/

    Saves the user's idle-return reason as a Disappearance and generates
    an AI reaction.

    Body:
        sessionId (str): Session UUID
        reasonType (str): youtube, laptops, ai_tools, startup, comments, other
        customReason (str, optional): Custom reason if 'other'
        idleDurationSeconds (float): How long the user was idle
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        reason_type = data.get('reasonType', 'other')
        custom_reason = data.get('customReason', '')
        idle_duration = data.get('idleDurationSeconds', 0)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        # Generate AI reaction
        result = generate_disappearance_response(
            reason_type, custom_reason or None, session.mood, session.interests
        )

        ai_response = result.get('data', 'You disappeared. The AI is impressed.') if result.get('success') else (
            f"You were gone for {int(idle_duration / 60)} minutes.\n"
            f"The AI was too busy procrastinating to comment."
        )

        disappearance = Disappearance.objects.create(
            session=session,
            disappearance_type=reason_type,
            custom_location=custom_reason if reason_type == 'other' else '',
            ai_response=ai_response,
        )

        return JsonResponse({
            'success': True,
            'data': {
                'disappearanceId': str(disappearance.id),
                'aiResponse': ai_response,
                'reasonType': reason_type,
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_recover_session(request):
    """
    GET /projects/procrastina-ai/api/recover-session/

    Returns the most recent active session for browser/server recovery.
    Called on page load when localStorage is empty or stale.
    """
    # Return the most recently created active session
    session = Session.objects.filter(is_active=True).order_by('-created_at').first()

    if not session:
        return JsonResponse({
            'success': True,
            'data': {'hasActiveSession': False}
        })

    return JsonResponse({
        'success': True,
        'data': {
            'hasActiveSession': True,
            'sessionId': str(session.id),
            'mood': session.mood,
            'interests': session.interests,
            'tasks': session.tasks,
            'createdAt': session.created_at.isoformat(),
            'activeSeconds': session.active_seconds,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_agent_disconnect(request):
    """
    POST /projects/procrastina-ai/api/agent-disconnect/

    Force-ends any active ActivitySession linked to this session.
    Called during 'Stop My Day' to cleanly disconnect the desktop agent.

    Body:
        sessionId (str): Parent Session UUID
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        active_agent = session.activity_sessions.filter(is_active=True).first()
        if not active_agent:
            return JsonResponse({
                'success': True,
                'data': {'hadActiveAgent': False, 'message': 'No active agent session.'}
            })

        result = desktop_integration.process_end_session({
            'activitySessionId': str(active_agent.id)
        })

        return JsonResponse({
            'success': True,
            'data': {
                'hadActiveAgent': True,
                'activitySessionId': str(active_agent.id),
                'endedCleanly': result.get('success', False),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================
# ACTIVITY TRACKING API — Desktop Agent
# ============================================================
# These endpoints are used by the Windows desktop agent.
# All POST endpoints are CSRF-exempt for external client compatibility.
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_activity_start_session(request):
    """
    Start a new activity tracking session.

    POST /projects/procrastina-ai/api/activity/start-session/

    Called by: Desktop agent on startup.
    Links to an existing manual Session (from 'Start My Day').
    Uses desktop_integration.py for validation and processing.

    Body:
        sessionId (str): Parent Session ID
        source (str): 'desktop_agent', 'browser_extension', 'manual_api'
        clientVersion (str): Version of the client software
        platform (str): OS platform (windows, macos, linux)
    """
    try:
        data = json.loads(request.body)

        result = desktop_integration.process_start_session(data)

        status_code = 201 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_end_session(request):
    """
    End an activity tracking session.

    POST /projects/procrastina-ai/api/activity/end-session/

    Called by: Desktop agent on shutdown, or when user clicks 'Stop My Day'.
    Uses desktop_integration.py for processing (auto-closes idle periods).

    Body:
        activitySessionId (str): ActivitySession ID to end
    """
    try:
        data = json.loads(request.body)

        result = desktop_integration.process_end_session(data)

        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_log(request):
    """
    Log one or more activity events.

    POST /projects/procrastina-ai/api/activity/log/

    Called by: Desktop agent on window change.
    Uses desktop_integration.py for normalization and processing.

    Single event body:
        activitySessionId (str): ActivitySession ID
        eventType (str): 'app_focus', 'website_visit', 'input_detected', etc.
        targetName (str): App name or website domain (raw process name OK)
        windowTitle (str, optional): Window title
        processName (str, optional): Raw process name
        category (str, optional): Auto-detected if omitted
        durationSeconds (float, optional): Duration of this event
        metadata (dict, optional): Extra data (window title, URL, etc.)

    Batch body (array):
        activitySessionId (str): ActivitySession ID
        events (list): Array of event objects
    """
    try:
        data = json.loads(request.body)

        # Check if this is a batch request
        events = data.get('events')
        if events and isinstance(events, list):
            result = desktop_integration.process_batch_events(data)
        else:
            result = desktop_integration.process_activity_event(data)

        status_code = 201 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_idle(request):
    """
    Log an idle period start (no user activity detected).

    POST /projects/procrastina-ai/api/activity/idle/

    Called by: Desktop agent when no keyboard/mouse input for threshold period.
    Uses desktop_integration.py for validation and processing.

    Body:
        activitySessionId (str): ActivitySession ID
        idleType (str): 'no_input', 'screen_locked', 'system_sleep', 'away'
        startedAt (str): ISO timestamp when idle started
        endedAt (str, optional): ISO timestamp when idle ended
        durationSeconds (float): Duration of idle period
        lastActiveApp (str, optional): App focused before idle
        lastActiveDomain (str, optional): Website active before idle
    """
    try:
        data = json.loads(request.body)

        result = desktop_integration.process_idle_start(data)

        status_code = 201 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_idle_end(request):
    """
    End an idle period (user resumed activity).

    POST /projects/procrastina-ai/api/activity/idle-end/

    Called by: Desktop agent when keyboard/mouse activity resumes.
    Uses desktop_integration.py for processing.

    Body:
        activitySessionId (str): ActivitySession ID
        endedAt (str): ISO timestamp when activity resumed
        durationSeconds (float): Actual idle duration
    """
    try:
        data = json.loads(request.body)

        result = desktop_integration.process_idle_end(data)

        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_report(request):
    """
    Generate an enhanced report combining manual + activity data.

    POST /projects/procrastina-ai/api/activity/report/

    Called by: Report generation when activity data is available.
    Falls back to manual-only report if no activity sessions exist.

    Body:
        sessionId (str): Parent Session ID

    Returns:
        AI summary + score + full analytics (apps, websites, idle time, etc.)
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')

        if not session_id:
            return JsonResponse(
                {'success': False, 'error': 'sessionId required'},
                status=400
            )

        result = activity_services.generate_enhanced_report(session_id)

        if not result.get('success'):
            return JsonResponse(result, status=400)

        # If session has a Report record, update it with the new score
        analytics = result.get('analytics', {})
        try:
            session = Session.objects.get(id=session_id)
            if not session.reports.exists():
                Report.objects.create(
                    session=session,
                    tasks_planned=len(analytics.get('tasks', [])),
                    tasks_completed=0,
                    total_disappearances=analytics.get('disCount', 0),
                    procrastination_score=result.get('score', 0),
                    ai_summary=result.get('data', ''),
                )
        except Session.DoesNotExist:
            pass

        return JsonResponse({
            'success': True,
            'data': {
                'aiSummary': result['data'],
                'score': result['score'],
                'analytics': analytics,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_activity_analytics(request):
    """
    Get comprehensive session analytics (manual + activity data).

    POST /projects/procrastina-ai/api/activity/analytics/

    Returns unified analytics: tasks, distractions, apps, websites, idle time.

    Body:
        sessionId (str): Parent Session ID
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')

        if not session_id:
            return JsonResponse(
                {'success': False, 'error': 'sessionId required'},
                status=400
            )

        result = activity_services.get_session_analytics(session_id)

        status_code = 200 if result['success'] else 400
        return JsonResponse(result, status=status_code)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

