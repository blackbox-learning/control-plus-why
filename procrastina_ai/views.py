"""
ProcrastinaAI Views - Page rendering and API endpoints

This module contains:
- Page views: Render HTML templates
- API views: Return JSON responses for frontend

All views are function-based and well-commented for beginners.
"""

import subprocess
import sys
import os
import signal as os_signal

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Session, Disappearance, Report, Prediction
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

    Generates a full-day procrastination forecast and stores it in the database.
    Uses previous disappearance history (if any) to improve prediction accuracy.
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

        # Get disappearance history for improved predictions
        history = [
            d.disappearance_type
            for d in session.disappearances.all()[:5]
        ]

        result = generate_prediction(mood, interests, tasks, history)

        if not result['success']:
            return JsonResponse({'success': False, 'error': 'Failed to generate prediction'}, status=500)

        # Store prediction in database for future report comparisons
        prediction_data = result['data']
        prediction_obj = Prediction.objects.create(
            session=session,
            forecast_summary=prediction_data.get('forecastSummary', ''),
            journey=prediction_data.get('journey', []),
            natural_breaks=prediction_data.get('naturalBreaks', []),
            metrics=prediction_data.get('metrics', {}),
            warnings=prediction_data.get('warnings', []),
            confidence=result.get('confidence', 94),
        )

        return JsonResponse({
            'success': True,
            'data': {
                'sessionId': str(session.id),
                'predictionId': str(prediction_obj.id),
                'forecastSummary': prediction_data.get('forecastSummary', ''),
                'journey': prediction_data.get('journey', []),
                'naturalBreaks': prediction_data.get('naturalBreaks', []),
                'metrics': prediction_data.get('metrics', {}),
                'warnings': prediction_data.get('warnings', []),
                'confidence': result.get('confidence', 94),
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

        # Use task_statuses from session if available (from Task Review step)
        task_statuses = session.task_statuses or {}
        if task_statuses:
            # Support both old format {task: "status"} and new format {task: {status, completion_score}}
            def _get_status(v):
                return v.get('status', v) if isinstance(v, dict) else v
            completed_count = sum(1 for v in task_statuses.values() if _get_status(v) == 'completed')
            tasks_completed = completed_count

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
                    tasks_planned, tasks_completed, disappearances, common_excuse,
                    task_statuses=session.task_statuses
                )
                score = result.get('score', 50)
                ai_summary = result.get('data', 'Report generation failed.')
        else:
            # Manual-only report (current behavior)
            result = generate_daily_report(
                tasks_planned, tasks_completed, disappearances, common_excuse,
                task_statuses=session.task_statuses
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
    BLOCKS if pending disappearances exist — forces resolution first.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        active_seconds = data.get('activeSeconds', 0)
        force_end = data.get('forceEnd', False)  # Allow forced end after resolution

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        # Check for pending disappearances (unless forceEnd is true)
        if not force_end:
            pending_count = session.disappearances.filter(explanation_status='pending').count()
            if pending_count > 0:
                return JsonResponse({
                    'success': False,
                    'hasPendingDisappearances': True,
                    'pendingCount': pending_count,
                    'error': f'You have {pending_count} unexplained disappearance(s). Please explain them before ending your day.'
                }, status=400)

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
        'taskStatuses': session.task_statuses or {},
        'pendingDisappearanceCount': disappearances.filter(explanation_status='pending').count(),
        'disappearances': [
            {
                'id': str(d.id),
                'type': d.disappearance_type,
                'customLocation': d.custom_location,
                'aiResponse': d.ai_response,
                'createdAt': d.created_at.isoformat(),
                'explanationStatus': d.explanation_status,
                'idleDurationSeconds': d.idle_duration_seconds,
                'lastActiveApp': d.last_active_app,
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

    # Calculate completion percentage from task statuses
    _ts = session.task_statuses or {}
    if _ts:
        def _get_score(v):
            if isinstance(v, dict) and 'completion_score' in v:
                return v['completion_score']
            _sm = {'completed': 100, 'in_progress': 75, 'partially_completed': 50, 'abandoned': 25, 'never_started': 0}
            _st = v.get('status', v) if isinstance(v, dict) else v
            return _sm.get(_st, 0)
        _scores = [_get_score(v) for v in _ts.values()]
        response_data['completionPercentage'] = round(sum(_scores) / len(_scores)) if _scores else 0
    else:
        response_data['completionPercentage'] = 0

    # Always include agent status so dashboard knows if agent is running or needs launching
    agent_status = desktop_integration.get_agent_status(session_id)
    response_data['agentStatus'] = agent_status

    # Include activity summary data if available (from desktop agent)
    has_activity = session.activity_sessions.exists()
    response_data['hasActivityData'] = has_activity

    if has_activity:

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
def api_pending_disappearances(request):
    """
    GET /projects/procrastina-ai/api/pending-disappearances/?sessionId=xxx

    Returns all pending (unexplained) disappearances for a session.
    Used by the dashboard to show the explanation queue and by the
    Stop My Day flow to force resolution.
    """
    session_id = request.GET.get('sessionId')
    if not session_id:
        return JsonResponse({'success': False, 'error': 'sessionId required'}, status=400)

    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

    pending = session.disappearances.filter(explanation_status='pending').order_by('created_at')

    return JsonResponse({
        'success': True,
        'data': {
            'pendingCount': pending.count(),
            'disappearances': [
                {
                    'id': str(d.id),
                    'type': d.disappearance_type,
                    'customLocation': d.custom_location,
                    'idleDurationSeconds': d.idle_duration_seconds,
                    'lastActiveApp': d.last_active_app,
                    'lastWindowTitle': d.last_window_title,
                    'createdAt': d.created_at.isoformat(),
                }
                for d in pending
            ]
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_explain_disappearance(request):
    """
    POST /projects/procrastina-ai/api/explain-disappearance/

    User explains a pending disappearance by selecting or typing a reason.
    Generates an AI response and marks the disappearance as 'explained'.

    Body:
        disappearanceId (str): Disappearance UUID
        reasonType (str): youtube, laptops, ai_tools, startup, comments, other
        customReason (str, optional): Custom reason text if 'other'
    """
    try:
        data = json.loads(request.body)
        disappearance_id = data.get('disappearanceId')
        reason_type = data.get('reasonType', 'other')
        custom_reason = data.get('customReason', '')

        if not disappearance_id:
            return JsonResponse({'success': False, 'error': 'disappearanceId required'}, status=400)

        try:
            disappearance = Disappearance.objects.get(id=disappearance_id)
        except Disappearance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Disappearance not found'}, status=404)

        session = disappearance.session

        # Generate AI reaction
        result = generate_disappearance_response(
            reason_type, custom_reason or None, session.mood, session.interests
        )

        ai_response = result.get('data', 'You disappeared. The AI is impressed.') if result.get('success') else (
            f"You were gone for {int(disappearance.idle_duration_seconds / 60)} minutes.\n"
            f"The AI was too busy procrastinating to comment."
        )

        # Update the disappearance record
        disappearance.disappearance_type = reason_type
        disappearance.custom_location = custom_reason if reason_type == 'other' else ''
        disappearance.ai_response = ai_response
        disappearance.explanation_status = 'explained'
        disappearance.explanation_timestamp = timezone.now()
        disappearance.reason_source = 'custom_text' if (reason_type == 'other' and custom_reason) else 'user_selected'
        disappearance.save()

        return JsonResponse({
            'success': True,
            'data': {
                'disappearanceId': str(disappearance.id),
                'aiResponse': ai_response,
                'reasonType': reason_type,
                'explanationStatus': 'explained',
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_skip_disappearance(request):
    """
    POST /projects/procrastina-ai/api/skip-disappearance/

    User chooses to 'Remain A Mystery' for a pending disappearance.
    Marks as 'unexplained' with no AI response.

    Body:
        disappearanceId (str): Disappearance UUID
    """
    try:
        data = json.loads(request.body)
        disappearance_id = data.get('disappearanceId')

        if not disappearance_id:
            return JsonResponse({'success': False, 'error': 'disappearanceId required'}, status=400)

        try:
            disappearance = Disappearance.objects.get(id=disappearance_id)
        except Disappearance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Disappearance not found'}, status=404)

        # Mark as unexplained — remains a mystery
        disappearance.explanation_status = 'unexplained'
        disappearance.explanation_timestamp = timezone.now()
        disappearance.disappearance_type = 'other'
        disappearance.custom_location = 'Unknown — Remained a Mystery'
        disappearance.ai_response = 'This disappearance remains classified. The AI respects your silence.'
        disappearance.save()

        return JsonResponse({
            'success': True,
            'data': {
                'disappearanceId': str(disappearance.id),
                'explanationStatus': 'unexplained',
                'message': 'This disappearance will remain a mystery.',
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_save_task_review(request):
    """
    POST /projects/procrastina-ai/api/save-task-review/

    Saves task completion statuses during the Stop My Day flow.

    Body:
        sessionId (str): Session UUID
        taskStatuses (dict): { task_name: {status, completion_score} }
            status values: completed, in_progress, partially_completed,
                           abandoned, never_started
            completion_score: 100, 75, 50, 25, 0 (auto-assigned by frontend)
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')
        task_statuses = data.get('taskStatuses', {})

        if not session_id:
            return JsonResponse({'success': False, 'error': 'sessionId required'}, status=400)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        session.task_statuses = task_statuses
        session.save(update_fields=['task_statuses', 'updated_at'])

        # Compute summary stats
        total = len(task_statuses)
        # Support both old format {task: "status"} and new format {task: {status, completion_score}}
        def _get_status(v):
            return v.get('status', v) if isinstance(v, dict) else v
        def _get_score(v):
            if isinstance(v, dict) and 'completion_score' in v:
                return v['completion_score']
            score_map = {'completed': 100, 'in_progress': 75, 'partially_completed': 50, 'abandoned': 25, 'never_started': 0}
            return score_map.get(_get_status(v), 0)

        completed = sum(1 for v in task_statuses.values() if _get_status(v) == 'completed')
        scores = [_get_score(v) for v in task_statuses.values()]
        pct = round(sum(scores) / len(scores)) if scores else 0

        return JsonResponse({
            'success': True,
            'data': {
                'tasksReviewed': total,
                'tasksCompleted': completed,
                'completionPercentage': pct,
            }
        })

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


# Track launched agent subprocess PIDs per session for management
_agent_processes = {}  # session_id -> pid


@csrf_exempt
@require_http_methods(["POST"])
def api_agent_launch(request):
    """
    POST /projects/procrastina-ai/api/agent-launch/

    Launches the desktop agent as a background subprocess.
    Called by the dashboard 'Launch Agent' button.

    Body:
        sessionId (str): Parent Session UUID
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('sessionId')

        if not session_id:
            return JsonResponse({'success': False, 'error': 'sessionId required'}, status=400)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)

        if not session.is_active:
            return JsonResponse({'success': False, 'error': 'Session is already ended'}, status=400)

        # Check if agent is already running for this session
        existing_agent = session.activity_sessions.filter(is_active=True).first()
        if existing_agent:
            return JsonResponse({
                'success': True,
                'data': {
                    'message': 'Agent is already running.',
                    'activitySessionId': str(existing_agent.id),
                    'alreadyRunning': True,
                }
            })

        # Locate the agent script
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agent_dir = os.path.join(project_root, 'procrastina_agent')
        agent_script = os.path.join(agent_dir, 'agent.py')

        if not os.path.isfile(agent_script):
            return JsonResponse({
                'success': False,
                'error': f'Agent script not found at {agent_script}'
            }, status=500)

        # Create logs directory
        logs_dir = os.path.join(agent_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, 'agent.log')

        # Launch agent as background subprocess
        try:
            log_fh = open(log_file, 'a', encoding='utf-8')
            proc = subprocess.Popen(
                [sys.executable, agent_script, str(session_id)],
                cwd=agent_dir,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0),
            )
            _agent_processes[session_id] = proc.pid
            log_fh.close()

            return JsonResponse({
                'success': True,
                'data': {
                    'message': 'Agent launched successfully.',
                    'pid': proc.pid,
                    'logFile': log_file,
                    'alreadyRunning': False,
                }
            }, status=201)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to launch agent: {str(e)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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

        # Kill the launched agent process if we launched it
        pid = _agent_processes.pop(session_id, None)
        if pid:
            try:
                os.kill(pid, os_signal.SIGTERM)
            except OSError:
                pass  # Process already exited

        return JsonResponse({
            'success': True,
            'data': {
                'hadActiveAgent': True,
                'activitySessionId': str(active_agent.id),
                'endedCleanly': result.get('success', False),
                'processKilled': pid is not None,
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

