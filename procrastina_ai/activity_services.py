"""
ProcrastinaAI Activity Services — Desktop Activity Processing Layer

This module handles all activity tracking logic for:
  - Python Desktop Agent (procrastina_agent/ — psutil, pynput, ctypes)
  - Browser Activity Tracker (script.js — mousemove, click, keydown, scroll)

CURRENT SYSTEM:
  Manual workflow: Start My Day → Prediction → I Got Distracted → Stop My Day → Report
  Uses: Session, Disappearance, Report models
  Frontend: Browser-based activity tracker (mousemove, click, keydown, scroll)

ACTIVITY TRACKING SYSTEM:
  Automated workflow: Desktop agent sends activity events
  Uses: ActivitySession, ActivityLog, ApplicationUsage, WebsiteUsage, IdlePeriod
  API: POST /api/activity/start-session, /log, /idle, /idle-end, /end-session, /report, /analytics

ARCHITECTURE:
  Views (views.py) → desktop_integration.py → activity_services.py → Models
  The service layer is isolated from views so the desktop tracking logic
  doesn't require changes to existing manual workflow views.

INTEGRATION POINTS:
  - Desktop Agent: Sends app_focus/app_blur events, idle detection, window changes
  - Browser Extension: Sends website_visit/website_leave events, tab activity
  - Both sources feed into the same ActivityLog → ApplicationUsage/WebsiteUsage pipeline
"""

from django.utils import timezone
from django.db.models import Sum, Count, Max, Min
from .models import (
    Session, ActivitySession, ActivityLog,
    ApplicationUsage, WebsiteUsage, IdlePeriod, Report,
)
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================
# KNOWN APP/WEBSITE CATEGORIES
# ============================================================
# Used to auto-categorize incoming activity events.
# Future desktop agent sends app names; we map them to categories.

APP_CATEGORY_MAP = {
    # Productivity / Development
    'visual studio code': 'development',
    'vscode': 'development',
    'code': 'development',
    'sublime text': 'development',
    'intellij': 'development',
    'pycharm': 'development',
    'terminal': 'development',
    'iterm': 'development',
    'cmd': 'development',
    'powershell': 'development',
    'notion': 'productivity',
    'obsidian': 'productivity',
    'google docs': 'productivity',
    'microsoft word': 'productivity',
    'microsoft excel': 'productivity',
    'figma': 'productivity',

    # Communication
    'slack': 'communication',
    'discord': 'communication',
    'zoom': 'communication',
    'teams': 'communication',
    'microsoft teams': 'communication',
    'telegram': 'communication',
    'whatsapp': 'communication',

    # Entertainment
    'spotify': 'entertainment',
    'vlc': 'entertainment',
    'steam': 'entertainment',
    'epic games': 'entertainment',

    # System
    'finder': 'system',
    'file explorer': 'system',
    'explorer': 'system',
    'desktop': 'system',
}

DOMAIN_CATEGORY_MAP = {
    # Social
    'instagram.com': 'social',
    'twitter.com': 'social',
    'x.com': 'social',
    'reddit.com': 'social',
    'facebook.com': 'social',
    'tiktok.com': 'social',
    'threads.net': 'social',
    'linkedin.com': 'social',

    # Entertainment
    'youtube.com': 'entertainment',
    'netflix.com': 'entertainment',
    'twitch.tv': 'entertainment',
    'hulu.com': 'entertainment',
    'disneyplus.com': 'entertainment',

    # AI Tools
    'chat.openai.com': 'ai_tools',
    'chatgpt.com': 'ai_tools',
    'claude.ai': 'ai_tools',
    'gemini.google.com': 'ai_tools',
    'perplexity.ai': 'ai_tools',
    'copilot.microsoft.com': 'ai_tools',

    # Productivity / Development
    'github.com': 'development',
    'gitlab.com': 'development',
    'stackoverflow.com': 'development',
    'notion.so': 'productivity',
    'docs.google.com': 'productivity',
    'figma.com': 'productivity',

    # Communication
    'mail.google.com': 'communication',
    'outlook.office.com': 'communication',
    'web.telegram.org': 'communication',
    'web.whatsapp.com': 'communication',
}


def _categorize_app(app_name):
    """Auto-categorize an application name into a known category."""
    key = app_name.lower().strip()
    for pattern, category in APP_CATEGORY_MAP.items():
        if pattern in key:
            return category
    return 'other'


def _categorize_domain(domain):
    """Auto-categorize a domain into a known category."""
    key = domain.lower().strip().replace('www.', '')
    for pattern, category in DOMAIN_CATEGORY_MAP.items():
        if pattern in key:
            return category
    return 'browsing'


# ============================================================
# ACTIVITY SESSION MANAGEMENT
# ============================================================

def start_activity_session(session_id, source='desktop_agent', client_version='', platform=''):
    """
    Start a new activity tracking session linked to an existing manual Session.

    Called by: Desktop agent on startup, browser extension on install/enable.

    Args:
        session_id (str/UUID): Parent Session ID (from manual 'Start My Day')
        source (str): 'desktop_agent', 'browser_extension', 'mobile_app', 'manual_api'
        client_version (str): Version of the client software
        platform (str): OS platform (windows, macos, linux)

    Returns:
        dict: {
            'success': bool,
            'data': {
                'activitySessionId': str,
                'sessionId': str,
                'startedAt': str (ISO),
            }
        }
    """
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return {'success': False, 'error': 'Parent session not found'}

    if not session.is_active:
        return {'success': False, 'error': 'Parent session is already ended'}

    activity_session = ActivitySession.objects.create(
        session=session,
        source=source,
        client_version=client_version,
        platform=platform,
    )

    return {
        'success': True,
        'data': {
            'activitySessionId': str(activity_session.id),
            'sessionId': str(session.id),
            'startedAt': activity_session.started_at.isoformat(),
        }
    }


def end_activity_session(activity_session_id):
    """
    End an activity tracking session.

    Called by: Desktop agent on shutdown, browser extension on disable, or
    when the user clicks 'Stop My Day'.

    Args:
        activity_session_id (str/UUID): ActivitySession ID

    Returns:
        dict: {
            'success': bool,
            'data': {
                'activitySessionId': str,
                'totalActiveSeconds': float,
                'totalIdleSeconds': float,
                'eventCount': int,
            }
        }
    """
    try:
        activity_session = ActivitySession.objects.get(id=activity_session_id)
    except ActivitySession.DoesNotExist:
        return {'success': False, 'error': 'Activity session not found'}

    if not activity_session.is_active:
        return {'success': False, 'error': 'Activity session already ended'}

    now = timezone.now()
    activity_session.ended_at = now
    activity_session.is_active = False

    # Recalculate totals from raw events
    totals = _calculate_session_totals(activity_session)
    activity_session.total_active_seconds = totals['active_seconds']
    activity_session.total_idle_seconds = totals['idle_seconds']
    activity_session.event_count = totals['event_count']
    activity_session.save()

    return {
        'success': True,
        'data': {
            'activitySessionId': str(activity_session.id),
            'totalActiveSeconds': activity_session.total_active_seconds,
            'totalIdleSeconds': activity_session.total_idle_seconds,
            'eventCount': activity_session.event_count,
        }
    }


# ============================================================
# ACTIVITY EVENT LOGGING
# ============================================================

def log_activity_event(activity_session_id, event_type, target_name,
                       category=None, duration_seconds=0, metadata=None):
    """
    Log a single activity event from a desktop agent or browser extension.

    Called by: Desktop agent on window focus change, browser extension on tab switch.

    Args:
        activity_session_id (str/UUID): ActivitySession ID
        event_type (str): One of ActivityLog.EVENT_TYPES
        target_name (str): App name or website domain
        category (str): Optional category override (auto-detected if None)
        duration_seconds (float): Duration of this event
        metadata (dict): Extra data (window title, URL path, etc.)

    Returns:
        dict: {
            'success': bool,
            'data': {
                'eventId': str,
                'event_type': str,
                'target_name': str,
                'category': str,
            }
        }
    """
    try:
        activity_session = ActivitySession.objects.get(id=activity_session_id)
    except ActivitySession.DoesNotExist:
        return {'success': False, 'error': 'Activity session not found'}

    if not activity_session.is_active:
        return {'success': False, 'error': 'Activity session is not active'}

    # Auto-categorize if not provided
    if not category:
        if event_type in ('website_visit', 'website_leave'):
            category = _categorize_domain(target_name)
        else:
            category = _categorize_app(target_name)

    event = ActivityLog.objects.create(
        activity_session=activity_session,
        event_type=event_type,
        target_name=target_name,
        category=category,
        duration_seconds=duration_seconds,
        metadata=metadata or {},
    )

    # Update aggregated usage tables
    _update_usage_aggregates(activity_session, event)

    # Update event count and running active-seconds total
    activity_session.event_count += 1
    if duration_seconds > 0:
        activity_session.total_active_seconds += duration_seconds
    activity_session.save(update_fields=[
        'event_count', 'total_active_seconds', 'updated_at',
    ])

    return {
        'success': True,
        'data': {
            'eventId': str(event.id),
            'eventType': event.event_type,
            'targetName': event.target_name,
            'category': event.category,
        }
    }


def log_batch_events(activity_session_id, events):
    """
    Log multiple activity events in a single call.
    More efficient for desktop agents that batch events.

    Args:
        activity_session_id (str/UUID): ActivitySession ID
        events (list[dict]): List of event dicts with keys:
            event_type, target_name, category (optional),
            duration_seconds (optional), metadata (optional)

    Returns:
        dict: {
            'success': bool,
            'data': {
                'loggedCount': int,
                'failedCount': int,
            }
        }
    """
    try:
        activity_session = ActivitySession.objects.get(id=activity_session_id)
    except ActivitySession.DoesNotExist:
        return {'success': False, 'error': 'Activity session not found'}

    if not activity_session.is_active:
        return {'success': False, 'error': 'Activity session is not active'}

    logged = 0
    failed = 0

    for ev in events:
        try:
            event_type = ev.get('event_type', 'input_detected')
            target_name = ev.get('target_name', 'unknown')
            category = ev.get('category') or (
                _categorize_domain(target_name)
                if event_type in ('website_visit', 'website_leave')
                else _categorize_app(target_name)
            )
            duration = ev.get('duration_seconds', 0)
            metadata = ev.get('metadata', {})

            event = ActivityLog.objects.create(
                activity_session=activity_session,
                event_type=event_type,
                target_name=target_name,
                category=category,
                duration_seconds=duration,
                metadata=metadata,
            )
            _update_usage_aggregates(activity_session, event)
            logged += 1
        except Exception as e:
            logger.error(f"Failed to log event in batch: {e}", exc_info=True)
            failed += 1

    # Update event count and running active-seconds total
    total_duration = sum(ev.get('duration_seconds', 0) for ev in events)
    activity_session.event_count += logged
    if total_duration > 0:
        activity_session.total_active_seconds += total_duration
    activity_session.save(update_fields=[
        'event_count', 'total_active_seconds', 'updated_at',
    ])

    return {
        'success': True,
        'data': {
            'loggedCount': logged,
            'failedCount': failed,
        }
    }


def log_idle_period(activity_session_id, idle_type, started_at, ended_at=None,
                    duration_seconds=0, last_active_app='', last_active_domain=''):
    """
    Log a detected idle period.

    Called by: Desktop agent when no input detected for threshold period.

    Args:
        activity_session_id (str/UUID): ActivitySession ID
        idle_type (str): 'no_input', 'screen_locked', 'system_sleep', 'away'
        started_at (str/datetime): When idle started (ISO format or datetime)
        ended_at (str/datetime): When idle ended (None if still idle)
        duration_seconds (float): Known duration
        last_active_app (str): App that was focused before idle
        last_active_domain (str): Website active before idle

    Returns:
        dict: {
            'success': bool,
            'data': {
                'idlePeriodId': str,
                'durationSeconds': float,
            }
        }
    """
    try:
        activity_session = ActivitySession.objects.get(id=activity_session_id)
    except ActivitySession.DoesNotExist:
        return {'success': False, 'error': 'Activity session not found'}

    # Parse datetime strings
    if isinstance(started_at, str):
        from django.utils.dateparse import parse_datetime
        started_at = parse_datetime(started_at) or timezone.now()

    if ended_at and isinstance(ended_at, str):
        from django.utils.dateparse import parse_datetime
        ended_at = parse_datetime(ended_at)

    idle = IdlePeriod.objects.create(
        activity_session=activity_session,
        idle_type=idle_type,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        last_active_app=last_active_app,
        last_active_domain=last_active_domain,
    )

    # Update idle total on the activity session.
    # Only add to running total if the idle period is already closed
    # (has ended_at). Open idle periods are counted when they end via
    # idle_end or auto-close during end_activity_session, preventing
    # double-counting.
    if ended_at and duration_seconds > 0:
        activity_session.total_idle_seconds += duration_seconds
        activity_session.save(update_fields=['total_idle_seconds', 'updated_at'])

    return {
        'success': True,
        'data': {
            'idlePeriodId': str(idle.id),
            'durationSeconds': duration_seconds,
        }
    }


# ============================================================
# USAGE AGGREGATION
# ============================================================

def _update_usage_aggregates(activity_session, event):
    """
    Update ApplicationUsage or WebsiteUsage based on an incoming event.
    Called internally after each event is logged.
    """
    now = event.timestamp

    if event.event_type in ('app_focus', 'app_blur', 'window_change'):
        # Update application usage
        usage, created = ApplicationUsage.objects.get_or_create(
            activity_session=activity_session,
            app_name=event.target_name,
            defaults={
                'category': event.category,
                'first_seen': now,
            }
        )
        if event.event_type == 'app_focus':
            usage.focus_events += 1
            usage.last_seen = now
            if created:
                usage.first_seen = now
        if event.duration_seconds > 0:
            usage.total_seconds += event.duration_seconds
        usage.save()

    elif event.event_type in ('website_visit', 'website_leave'):
        # Update website usage
        usage, created = WebsiteUsage.objects.get_or_create(
            activity_session=activity_session,
            domain=event.target_name,
            defaults={
                'category': event.category,
                'first_seen': now,
            }
        )
        if event.event_type == 'website_visit':
            usage.visit_count += 1
            usage.last_seen = now
            if created:
                usage.first_seen = now
        if event.duration_seconds > 0:
            usage.total_seconds += event.duration_seconds
        usage.save()


def _calculate_session_totals(activity_session):
    """Calculate aggregated totals from raw events for an activity session.

    This is the authoritative source for session totals, called during
    end_activity_session(). It recomputes everything from raw DB records
    so the final values are always accurate regardless of incremental
    updates that may have occurred during the session.
    """
    events = activity_session.events.all()

    # Total active time: sum of all event durations
    active_seconds = events.aggregate(
        total=Sum('duration_seconds')
    )['total'] or 0

    # Total idle time: sum of all closed idle periods only.
    # Open (unended) idle periods are excluded to avoid inflated values.
    idle_seconds = activity_session.idle_periods.filter(
        ended_at__isnull=False,
    ).aggregate(
        total=Sum('duration_seconds')
    )['total'] or 0

    event_count = events.count()

    return {
        'active_seconds': active_seconds,
        'idle_seconds': idle_seconds,
        'event_count': event_count,
    }


def get_activity_timeline(activity_session_id, limit=50):
    """
    Build a chronological timeline of activity events for an activity session.

    Returns a simplified list of events showing what the user did over time:
    VS Code → Chrome → YouTube → VS Code → Idle → Chrome

    Used by the report to show "What Actually Happened" with real data.

    Args:
        activity_session_id (str/UUID): ActivitySession ID
        limit (int): Max events to return (default 50)

    Returns:
        list[dict]: [
            {
                'type': 'app' | 'website' | 'idle',
                'name': str,
                'category': str,
                'timestamp': str (ISO),
                'durationSeconds': float,
            }
        ]
    """
    try:
        act_session = ActivitySession.objects.get(id=activity_session_id)
    except ActivitySession.DoesNotExist:
        return []

    # Get app_focus events (main timeline markers)
    focus_events = act_session.events.filter(
        event_type__in=['app_focus', 'website_visit']
    ).order_by('timestamp')[:limit]

    # Get idle periods
    idle_periods = act_session.idle_periods.all().order_by('started_at')

    # Merge into a single timeline
    timeline = []

    for ev in focus_events:
        timeline.append({
            'type': 'app' if ev.event_type == 'app_focus' else 'website',
            'name': ev.target_name,
            'category': ev.category,
            'timestamp': ev.timestamp.isoformat(),
            'durationSeconds': ev.duration_seconds,
        })

    for idle in idle_periods:
        timeline.append({
            'type': 'idle',
            'name': f'Idle ({idle.get_idle_type_display()})',
            'category': 'system',
            'timestamp': idle.started_at.isoformat(),
            'durationSeconds': idle.duration_seconds,
        })

    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'])

    # Deduplicate consecutive same-name entries
    deduped = []
    for item in timeline:
        if not deduped or deduped[-1]['name'] != item['name'] or item['type'] == 'idle':
            deduped.append(item)

    return deduped[:limit]


# ============================================================
# SESSION ANALYTICS
# ============================================================

def get_session_analytics(session_id):
    """
    Get comprehensive analytics for a session, combining:
    - Manual distraction data (current system)
    - Desktop activity data (future system, if available)

    Returns a unified analytics dict that the report can use.

    This is the key function that bridges the two data sources.
    Current reports use manual data. Future reports can use
    activity data when available, falling back to manual data.

    Args:
        session_id (str/UUID): Session ID

    Returns:
        dict: {
            'success': bool,
            'data': {
                # Manual data (always available)
                'tasks': list,
                'disappearances': list,
                'disCount': int,
                'commonExcuse': str,
                'breakdown': dict,
                # Activity data (if desktop agent/extension connected)
                'hasActivityData': bool,
                'sessionLengthSeconds': float,
                'activeSeconds': float,
                'idleSeconds': float,
                'topApps': list,
                'topWebsites': list,
                'categoryBreakdown': dict,
                'idlePeriods': list,
                # Computed
                'productivityRatio': float,  # 0-1, higher = more productive
                'distractionScore': int,     # 0-100
            }
        }
    """
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return {'success': False, 'error': 'Session not found'}

    # --- Manual data (current system) ---
    disappearances = session.disappearances.all()
    type_counts = {}
    for d in disappearances:
        t = d.disappearance_type
        type_counts[t] = type_counts.get(t, 0) + 1
    common_excuse = max(type_counts, key=type_counts.get) if type_counts else 'Unknown'

    # Explanation status counts
    explained_count = disappearances.filter(explanation_status='explained').count()
    unexplained_count = disappearances.filter(explanation_status='unexplained').count()
    pending_count = disappearances.filter(explanation_status='pending').count()

    # --- Activity data (future system) ---
    activity_sessions = session.activity_sessions.all()
    has_activity = activity_sessions.exists()

    top_apps = []
    top_websites = []
    category_breakdown = {}
    idle_periods = []
    activity_timeline = []
    total_active = 0
    total_idle = 0
    agent_connected = False
    current_app = ''
    focus_changes = 0

    if has_activity:
        # Aggregate across all activity sessions for this manual session
        for act_session in activity_sessions:
            # Track agent status from most recent active session
            if act_session.is_active:
                agent_connected = True
                current_app = act_session.last_active_app
            focus_changes += act_session.focus_change_count

            # Top applications
            apps = act_session.application_usage.all().order_by('-total_seconds')[:10]
            for app in apps:
                top_apps.append({
                    'name': app.app_name,
                    'category': app.category,
                    'totalSeconds': app.total_seconds,
                    'focusEvents': app.focus_events,
                })

            # Top websites
            sites = act_session.website_usage.all().order_by('-total_seconds')[:10]
            for site in sites:
                top_websites.append({
                    'domain': site.domain,
                    'category': site.category,
                    'totalSeconds': site.total_seconds,
                    'visitCount': site.visit_count,
                })

            # Category breakdown
            events = act_session.events.values('category').annotate(
                total_time=Sum('duration_seconds'),
                count=Count('id')
            )
            for cat in events:
                c = cat['category']
                if c not in category_breakdown:
                    category_breakdown[c] = {'seconds': 0, 'events': 0}
                category_breakdown[c]['seconds'] += cat['total_time'] or 0
                category_breakdown[c]['events'] += cat['count']

            # Idle periods
            idles = act_session.idle_periods.all()
            for idle in idles:
                idle_periods.append({
                    'type': idle.idle_type,
                    'typeDisplay': idle.get_idle_type_display(),
                    'durationSeconds': idle.duration_seconds,
                    'startedAt': idle.started_at.isoformat(),
                    'endedAt': idle.ended_at.isoformat() if idle.ended_at else None,
                    'lastApp': idle.last_active_app,
                    'lastDomain': idle.last_active_domain,
                })

            # Activity timeline
            timeline = get_activity_timeline(act_session.id)
            activity_timeline.extend(timeline)

            total_active += act_session.total_active_seconds
            total_idle += act_session.total_idle_seconds

    # Session length
    ended = session.ended_at or timezone.now()
    session_length = (ended - session.created_at).total_seconds()

    # Productivity ratio (0-1): time in productivity apps vs total
    productive_seconds = sum(
        cat['seconds'] for cat_name, cat in category_breakdown.items()
        if cat_name in ('productivity', 'development')
    )
    productivity_ratio = (
        productive_seconds / max(total_active, 1) if total_active > 0 else 0
    )

    # Distraction score (0-100)
    # Combines manual distractions + activity-based distractions
    manual_score = min(100, disappearances.count() * 10)
    activity_distraction_seconds = sum(
        cat['seconds'] for cat_name, cat in category_breakdown.items()
        if cat_name in ('social', 'entertainment', 'ai_tools')
    )
    # Scale activity distraction: 1 hour of social media = 50 points
    activity_score = min(100, int(activity_distraction_seconds / 36 * 100 / 100))
    # Weighted combination (manual gets more weight for now since it's explicit)
    distraction_score = min(100, int(manual_score * 0.6 + activity_score * 0.4))

    return {
        'success': True,
        'data': {
            # Manual data
            'tasks': session.tasks,
            'disappearances': [
                {
                    'type': d.disappearance_type,
                    'aiResponse': d.ai_response,
                    'createdAt': d.created_at.isoformat(),
                }
                for d in disappearances
            ],
            'disCount': disappearances.count(),
            'explainedCount': explained_count,
            'unexplainedCount': unexplained_count,
            'pendingCount': pending_count,
            'commonExcuse': common_excuse,
            'breakdown': type_counts,
            # Activity data
            'hasActivityData': has_activity,
            'agentConnected': agent_connected,
            'currentApp': current_app,
            'focusChanges': focus_changes,
            'sessionLengthSeconds': session_length,
            'activeSeconds': total_active or session.active_seconds,
            'idleSeconds': total_idle,
            'topApps': top_apps,
            'topWebsites': top_websites,
            'categoryBreakdown': category_breakdown,
            'idlePeriods': idle_periods,
            'activityTimeline': activity_timeline,
            # Task completion data
            'taskStatuses': session.task_statuses or {},
            # Computed
            'productivityRatio': round(productivity_ratio, 2),
            'distractionScore': distraction_score,
        }
    }


# ============================================================
# ENHANCED REPORT GENERATION
# ============================================================

def generate_enhanced_report(session_id):
    """
    Generate a report that combines manual distraction data with
    desktop activity data (when available).

    CURRENT BEHAVIOR (no activity data):
    - Uses manual disappearances, tasks, common excuse
    - Same as existing generate_daily_report in services.py

    FUTURE BEHAVIOR (with activity data):
    - Adds top apps, top websites, idle time, category breakdown
    - AI summary includes real usage data ("You spent 2h on YouTube")
    - Productivity ratio and distraction score from real data

    This function is called by the report generation API.
    The existing frontend report.html already handles the data.

    Args:
        session_id (str/UUID): Session ID

    Returns:
        dict: {
            'success': bool,
            'data': str (AI summary text),
            'score': int (0-100),
            'analytics': dict (full analytics data),
        }
    """
    analytics_result = get_session_analytics(session_id)
    if not analytics_result['success']:
        return analytics_result

    analytics = analytics_result['data']

    # Build AI prompt based on available data
    if analytics['hasActivityData']:
        prompt = _build_activity_report_prompt(analytics)
    else:
        prompt = _build_manual_report_prompt(analytics)

    # Call AI (reuse the _call_ai function from services.py)
    from .services import _call_ai
    try:
        ai_text = _call_ai(prompt, temperature=0.8, max_tokens=250)
    except Exception as e:
        ai_text = f"Report generation failed: {str(e)}"

    # Calculate score
    tasks_planned = len(analytics['tasks'])
    disappearances = analytics['disCount']
    score = analytics['distractionScore']

    return {
        'success': True,
        'data': ai_text,
        'score': score,
        'analytics': analytics,
    }


def _build_task_detail(analytics):
    """Build task completion detail string from taskStatuses.
    Supports both old format {task: "status"} and new format {task: {status, completion_score}}.
    """
    task_statuses = analytics.get('taskStatuses', {})
    if not task_statuses:
        return '', 0
    from collections import Counter

    def _get_status(v):
        return v.get('status', v) if isinstance(v, dict) else v

    def _get_score(v):
        if isinstance(v, dict) and 'completion_score' in v:
            return v['completion_score']
        score_map = {'completed': 100, 'in_progress': 75, 'partially_completed': 50, 'abandoned': 25, 'never_started': 0}
        return score_map.get(_get_status(v), 0)

    statuses = [_get_status(v) for v in task_statuses.values()]
    scores = [_get_score(v) for v in task_statuses.values()]
    counts = Counter(statuses)
    completion_percentage = round(sum(scores) / len(scores)) if scores else 0

    status_labels = {
        'completed': 'completed',
        'in_progress': 'still in progress',
        'partially_completed': 'partially completed',
        'abandoned': 'abandoned',
        'never_started': 'never started',
    }
    parts = []
    for key, label in status_labels.items():
        c = counts.get(key, 0)
        if c > 0:
            parts.append(f'{c} {label}')
    detail = f'\nTask breakdown: {", ".join(parts)}.'
    detail += f'\nOverall completion: {completion_percentage}%.'
    task_lines = '\n'.join(
        f'- {name}: {status_labels.get(_get_status(v), _get_status(v))} (score: {_get_score(v)})'
        for name, v in task_statuses.items()
    )
    detail += f'\n{task_lines}'
    return detail, completion_percentage


def _build_manual_report_prompt(analytics):
    """Build AI prompt for manual-only report (current system)."""
    explained = analytics.get('explainedCount', 0)
    unexplained = analytics.get('unexplainedCount', 0)
    explanation_text = ''
    if analytics['disCount'] > 0:
        explanation_text = f"\n- {explained} were explained, {unexplained} remain a mystery"
    task_detail, completion_pct = _build_task_detail(analytics)

    # Focus changes
    focus_changes = analytics.get('focusChanges', 0)
    focus_text = f'\nFocus changes: {focus_changes}' if focus_changes > 0 else ''

    return f"""You are a funny friend writing someone's end-of-day summary.

Today's stats:
- Tasks planned: {len(analytics['tasks'])}
- Overall completion: {completion_pct}%
- Times they got distracted: {analytics['disCount']}{explanation_text}
- Go-to distraction: {analytics['commonExcuse']}{focus_text}{task_detail}

Write a SHORT summary (3-5 lines max).

RULES:
- Each line = one short sentence
- Use line breaks between lines
- Use simple words a kid would understand
- Be funny but kind
- Tease them, don't make them feel bad
- Add a tiny compliment or "respect" moment
- Reference specific tasks and their statuses when possible
- Mention the completion percentage naturally
{'' if not unexplained else '- Mention the unexplained disappearances in a funny way (e.g., "classified incidents")'}

Only return the summary. No intro, no labels."""


def _build_activity_report_prompt(analytics):
    """
    Build AI prompt for activity-enhanced report (future system).
    Includes real app/website usage data from desktop agent.
    """
    # Format top apps
    top_apps_text = ''
    if analytics['topApps']:
        app_lines = []
        for app in analytics['topApps'][:5]:
            mins = int(app['totalSeconds'] / 60)
            app_lines.append(f"  - {app['name']} ({app['category']}): {mins} min")
        top_apps_text = 'Top applications:\n' + '\n'.join(app_lines)

    # Format top websites
    top_sites_text = ''
    if analytics['topWebsites']:
        site_lines = []
        for site in analytics['topWebsites'][:5]:
            mins = int(site['totalSeconds'] / 60)
            site_lines.append(f"  - {site['domain']} ({site['category']}): {mins} min, {site['visitCount']} visits")
        top_sites_text = 'Top websites:\n' + '\n'.join(site_lines)

    # Active vs idle
    active_mins = int(analytics['activeSeconds'] / 60)
    idle_mins = int(analytics['idleSeconds'] / 60)
    session_mins = int(analytics['sessionLengthSeconds'] / 60)

    # Explanation stats
    explained = analytics.get('explainedCount', 0)
    unexplained = analytics.get('unexplainedCount', 0)
    explanation_text = ''
    if analytics['disCount'] > 0:
        explanation_text = f"\nDisappearances: {explained} explained, {unexplained} remain a mystery"

    task_detail, completion_pct = _build_task_detail(analytics)

    # Focus changes
    focus_changes = analytics.get('focusChanges', 0)

    # Activity timeline summary
    timeline = analytics.get('activityTimeline', [])
    timeline_text = ''
    if timeline:
        apps_used = set(item['name'] for item in timeline if item['type'] == 'app')
        if apps_used:
            timeline_text = f'\nApps used: {", ".join(list(apps_used)[:5])}'

    return f"""You are a funny friend writing someone's end-of-day report.
You have REAL data about what they actually did today.

Session: {session_mins} minutes total
Active time: {active_mins} minutes
Idle time: {idle_mins} minutes
Tasks planned: {len(analytics['tasks'])}
Overall task completion: {completion_pct}%
Manual distractions logged: {analytics['disCount']}{explanation_text}
Focus changes: {focus_changes}
Productivity ratio: {int(analytics['productivityRatio'] * 100)}%{timeline_text}{task_detail}

{top_apps_text}

{top_sites_text}

Write a SHORT funny summary (4-6 lines max).

RULES:
- Each line = one short sentence
- Use line breaks between lines
- Reference SPECIFIC apps/websites from the data (e.g., "You spent 45 min on YouTube")
- Reference specific tasks and their statuses when possible
- Mention the completion percentage naturally
- Use simple words
- Be funny but kind
- Tease them about their actual behavior
- End with a tiny compliment
{'' if not unexplained else '- Mention the unexplained disappearances humorously (e.g., "classified incidents" or "mysterious vanishances")'}

Only return the summary. No intro, no labels."""

