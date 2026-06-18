"""
ProcrastinaAI Desktop Integration Layer

This module is the entry point for all incoming desktop agent events.
It validates, normalizes, and processes activity payloads before
passing them to activity_services.py for storage.

DESKTOP AGENT FLOW:
  Desktop Agent (procrastina_agent/ — psutil + pynput + ctypes)
    ↓
  desktop_integration.py (validate, normalize, categorize)
    ↓
  activity_services.py (store events, aggregate usage)
    ↓
  Database (ActivitySession, ActivityLog, ApplicationUsage, IdlePeriod)
    ↓
  Report Generation (enhanced AI reports with real data)

RESPONSIBILITIES:
  - Validate incoming activity event payloads
  - Normalize application names (e.g., 'Code.exe' → 'Visual Studio Code')
  - Auto-categorize apps and websites into known categories
  - Detect and log focus switches between applications
  - Detect and manage idle periods
  - Aggregate activity into meaningful summaries
  - Sync activity data with the parent Session model

EVENT SCHEMA:
  All events from the desktop agent must include:
  {
    "sessionId": "<parent Session UUID>",          // required
    "activitySessionId": "<ActivitySession UUID>", // required after start-session
    "eventType": "app_focus | app_blur | input_detected | window_change",
    "targetName": "Visual Studio Code",            // app name or domain
    "windowTitle": "main.py — my-project",         // optional window title
    "durationSeconds": 120.5,                      // optional duration
    "metadata": { ... }                            // optional extra data
  }

SUPPORTED EVENT TYPES:
  - start_session: Agent connects, begins tracking
  - app_focus: Application gained focus
  - app_blur: Application lost focus
  - window_change: Active window changed
  - input_detected: Keyboard/mouse activity burst
  - idle_start: No input detected for threshold
  - idle_end: Input resumed after idle
  - end_session: Agent disconnects, stops tracking

NORMALIZATION MAP:
  Process names from the OS are mapped to friendly names:
    code.exe         → Visual Studio Code
    chrome.exe       → Google Chrome
    spotify.exe      → Spotify
    discord.exe      → Discord
    explorer.exe     → File Explorer
    windowsTerminal  → Terminal
    ...
"""

from django.utils import timezone
from django.utils.dateparse import parse_datetime
import logging
from . import activity_services
from .models import Session, ActivitySession, Disappearance

logger = logging.getLogger(__name__)


# ============================================================
# APPLICATION NAME NORMALIZATION
# ============================================================
# Maps OS process names and window class names to friendly display names.
# The desktop agent sends raw process names; we convert them here.

PROCESS_NAME_MAP = {
    # Windows process names
    'code.exe': 'Visual Studio Code',
    'code': 'Visual Studio Code',
    'vscode.exe': 'Visual Studio Code',
    'chrome.exe': 'Google Chrome',
    'chrome': 'Google Chrome',
    'firefox.exe': 'Firefox',
    'firefox': 'Firefox',
    'msedge.exe': 'Microsoft Edge',
    'edge.exe': 'Microsoft Edge',
    'opera.exe': 'Opera',
    'brave.exe': 'Brave',
    'spotify.exe': 'Spotify',
    'discord.exe': 'Discord',
    'slack.exe': 'Slack',
    'teams.exe': 'Microsoft Teams',
    'zoom.exe': 'Zoom',
    'telegram.exe': 'Telegram',
    'whatsapp.exe': 'WhatsApp',
    'notion.exe': 'Notion',
    'obsidian.exe': 'Obsidian',
    'figma.exe': 'Figma',
    'steam.exe': 'Steam',
    'epicgameslauncher.exe': 'Epic Games',
    'vlc.exe': 'VLC',
    'explorer.exe': 'File Explorer',
    'windowsterminal.exe': 'Terminal',
    'wt.exe': 'Terminal',
    'cmd.exe': 'Terminal',
    'powershell.exe': 'Terminal',
    'conhost.exe': 'Terminal',
    'word.exe': 'Microsoft Word',
    'winword.exe': 'Microsoft Word',
    'excel.exe': 'Microsoft Excel',
    'powerpnt.exe': 'Microsoft PowerPoint',
    'onenote.exe': 'Microsoft OneNote',
    'outlook.exe': 'Microsoft Outlook',

    # macOS process names
    'com.apple.finder': 'Finder',
    'com.apple.safari': 'Safari',
    'com.google.chrome': 'Google Chrome',
    'com.microsoft.vscode': 'Visual Studio Code',
    'com.spotify.client': 'Spotify',
    'com.tinyspeck.slackmacgap': 'Slack',
    'com.discordapp.discord': 'Discord',
    'com.apple.mail': 'Apple Mail',
    'com.apple.terminal': 'Terminal',
    'com.googlecode.iterm2': 'iTerm',

    # Linux process names
    'gnome-terminal': 'Terminal',
    'konsole': 'Terminal',
    'xterm': 'Terminal',
    'thunar': 'File Explorer',
    'nautilus': 'File Explorer',
    'dolphin': 'File Explorer',
}

# Map for normalizing common app display names to a canonical form
CANONICAL_NAME_MAP = {
    'visual studio code': 'Visual Studio Code',
    'vs code': 'Visual Studio Code',
    'vscode': 'Visual Studio Code',
    'google chrome': 'Google Chrome',
    'chrome': 'Google Chrome',
    'microsoft edge': 'Microsoft Edge',
    'edge': 'Microsoft Edge',
    'microsoft teams': 'Microsoft Teams',
    'ms teams': 'Microsoft Teams',
    'file explorer': 'File Explorer',
    'windows explorer': 'File Explorer',
    'windows terminal': 'Terminal',
    'command prompt': 'Terminal',
}


def normalize_app_name(raw_name):
    """
    Normalize a raw process name or app name to a friendly display name.

    Examples:
        'code.exe' → 'Visual Studio Code'
        'chrome.exe' → 'Google Chrome'
        'VS Code' → 'Visual Studio Code'
        'myapp.exe' → 'myapp' (fallback: strip extension)
    """
    if not raw_name:
        return 'Unknown'

    key = raw_name.lower().strip()

    # 1. Check process name map
    if key in PROCESS_NAME_MAP:
        return PROCESS_NAME_MAP[key]

    # 2. Check canonical name map
    if key in CANONICAL_NAME_MAP:
        return CANONICAL_NAME_MAP[key]

    # 3. Fallback: strip .exe/.app extension, title-case
    name = raw_name
    for ext in ('.exe', '.app', '.desktop', '.lnk'):
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
            break

    return name.strip() or 'Unknown'


# ============================================================
# EVENT VALIDATION
# ============================================================

VALID_EVENT_TYPES = {
    'app_focus', 'app_blur', 'window_change',
    'input_detected', 'website_visit', 'website_leave',
    'system_event',
}

VALID_IDLE_TYPES = {'no_input', 'screen_locked', 'system_sleep', 'away'}


def validate_event_payload(data):
    """
    Validate an incoming activity event payload.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    if not data.get('activitySessionId'):
        errors.append('activitySessionId is required')

    event_type = data.get('eventType', 'input_detected')
    if event_type not in VALID_EVENT_TYPES:
        errors.append(f'Invalid eventType: {event_type}')

    # app_focus/window_change require targetName
    if event_type in ('app_focus', 'app_blur', 'window_change'):
        if not data.get('targetName'):
            errors.append(f'targetName required for {event_type}')

    return (len(errors) == 0, errors)


def validate_idle_payload(data):
    """Validate an incoming idle event payload."""
    errors = []

    if not data.get('activitySessionId'):
        errors.append('activitySessionId is required')

    idle_type = data.get('idleType', 'no_input')
    if idle_type not in VALID_IDLE_TYPES:
        errors.append(f'Invalid idleType: {idle_type}')

    if not data.get('startedAt'):
        errors.append('startedAt is required')

    return (len(errors) == 0, errors)


def validate_start_session_payload(data):
    """Validate a start-session payload."""
    errors = []

    if not data.get('sessionId'):
        errors.append('sessionId is required (parent Session UUID)')

    source = data.get('source', 'desktop_agent')
    valid_sources = [s[0] for s in ActivitySession.SOURCE_CHOICES]
    if source not in valid_sources:
        errors.append(f'Invalid source: {source}')

    return (len(errors) == 0, errors)


# ============================================================
# EVENT PROCESSING — Main Entry Points
# ============================================================

def process_start_session(data):
    """
    Process a desktop agent start-session request.

    Validates payload, creates ActivitySession, returns session info.

    Args:
        data (dict): {
            sessionId (str): Parent Session UUID
            source (str): 'desktop_agent' (default)
            clientVersion (str): Agent version
            platform (str): OS platform
        }

    Returns:
        dict: {
            'success': bool,
            'data': {
                'activitySessionId': str,
                'sessionId': str,
                'startedAt': str,
            }
        }
    """
    is_valid, errors = validate_start_session_payload(data)
    if not is_valid:
        return {'success': False, 'error': '; '.join(errors)}

    return activity_services.start_activity_session(
        session_id=data['sessionId'],
        source=data.get('source', 'desktop_agent'),
        client_version=data.get('clientVersion', ''),
        platform=data.get('platform', ''),
    )


def process_activity_event(data):
    """
    Process a single activity event from the desktop agent.

    Validates, normalizes app name, auto-categorizes, stores event,
    and updates focus tracking on the ActivitySession.

    Args:
        data (dict): Event payload (see module docstring for schema)

    Returns:
        dict: {
            'success': bool,
            'data': {
                'eventId': str,
                'eventType': str,
                'targetName': str (normalized),
                'category': str,
                'focusChanged': bool,
            }
        }
    """
    is_valid, errors = validate_event_payload(data)
    if not is_valid:
        return {'success': False, 'error': '; '.join(errors)}

    activity_session_id = data['activitySessionId']
    event_type = data.get('eventType', 'input_detected')

    # Normalize application name
    raw_name = data.get('targetName', 'unknown')
    normalized_name = normalize_app_name(raw_name)

    # Build enriched metadata
    metadata = data.get('metadata') or {}
    metadata['raw_name'] = raw_name
    if data.get('windowTitle'):
        metadata['window_title'] = data['windowTitle']
    if data.get('processName'):
        metadata['process_name'] = data['processName']

    # Detect focus change
    focus_changed = False
    if event_type == 'app_focus':
        try:
            act_session = ActivitySession.objects.get(id=activity_session_id)
            prev_app = act_session.last_active_app
            if prev_app and prev_app != normalized_name:
                focus_changed = True
                act_session.focus_change_count += 1
            act_session.last_active_app = normalized_name
            act_session.save(update_fields=[
                'last_active_app', 'focus_change_count', 'updated_at'
            ])
        except ActivitySession.DoesNotExist:
            logger.error(
                f"ActivitySession not found during focus detection: {activity_session_id}"
            )

    # Store event via activity_services
    result = activity_services.log_activity_event(
        activity_session_id=activity_session_id,
        event_type=event_type,
        target_name=normalized_name,
        category=data.get('category'),  # auto-detected if None
        duration_seconds=data.get('durationSeconds', 0),
        metadata=metadata,
    )

    # Add focus_changed flag to result
    if result['success']:
        result['data']['focusChanged'] = focus_changed

    return result


def process_batch_events(data):
    """
    Process multiple events in a single call.

    More efficient for agents that batch events before sending.

    Args:
        data (dict): {
            activitySessionId (str): ActivitySession UUID,
            events (list): List of event objects
        }

    Returns:
        dict: {
            'success': bool,
            'data': {
                'loggedCount': int,
                'failedCount': int,
                'focusChanges': int,
            }
        }
    """
    activity_session_id = data.get('activitySessionId')
    if not activity_session_id:
        return {'success': False, 'error': 'activitySessionId required'}

    events = data.get('events', [])
    if not events:
        return {'success': False, 'error': 'No events provided'}

    # Normalize each event before batch logging
    focus_changes = 0
    normalized_events = []
    for ev in events:
        raw_name = ev.get('target_name', ev.get('targetName', 'unknown'))
        ev['target_name'] = normalize_app_name(raw_name)

        metadata = ev.get('metadata') or {}
        metadata['raw_name'] = raw_name
        if ev.get('windowTitle'):
            metadata['window_title'] = ev['windowTitle']
        ev['metadata'] = metadata

        # Map camelCase to snake_case for activity_services
        if 'eventType' in ev:
            ev['event_type'] = ev.pop('eventType')
        if 'targetName' in ev:
            ev['target_name'] = normalize_app_name(ev.pop('targetName'))
        if 'durationSeconds' in ev:
            ev['duration_seconds'] = ev.pop('durationSeconds')

        if ev.get('event_type') == 'app_focus':
            focus_changes += 1

        normalized_events.append(ev)

    result = activity_services.log_batch_events(
        activity_session_id, normalized_events
    )

    if result['success']:
        # Update focus tracking on activity session
        try:
            act_session = ActivitySession.objects.get(id=activity_session_id)
            act_session.focus_change_count += focus_changes
            if normalized_events:
                last = normalized_events[-1]
                if last.get('event_type') == 'app_focus':
                    act_session.last_active_app = last.get('target_name', '')
            act_session.save(update_fields=[
                'focus_change_count', 'last_active_app', 'updated_at'
            ])
        except ActivitySession.DoesNotExist:
            logger.error(
                f"ActivitySession not found during batch focus update: {activity_session_id}"
            )

        result['data']['focusChanges'] = focus_changes

    return result


def process_idle_start(data):
    """
    Process an idle-start event from the desktop agent.

    Called when no keyboard/mouse input is detected for the configured
    threshold (default: 5 minutes).

    Args:
        data (dict): {
            activitySessionId (str): ActivitySession UUID,
            idleType (str): 'no_input' | 'screen_locked' | 'system_sleep' | 'away',
            startedAt (str): ISO timestamp,
            lastActiveApp (str): App focused before idle,
            lastActiveDomain (str): Website active before idle,
        }

    Returns:
        dict: Result from activity_services.log_idle_period
    """
    is_valid, errors = validate_idle_payload(data)
    if not is_valid:
        return {'success': False, 'error': '; '.join(errors)}

    activity_session_id = data['activitySessionId']

    # Normalize last active app name
    last_app = data.get('lastActiveApp', '')
    if last_app:
        last_app = normalize_app_name(last_app)

    # Mark idle start on activity session
    started_at = data.get('startedAt', timezone.now().isoformat())
    try:
        act_session = ActivitySession.objects.get(id=activity_session_id)
        if isinstance(started_at, str):
            act_session.last_idle_started = parse_datetime(started_at) or timezone.now()
        else:
            act_session.last_idle_started = started_at
        act_session.save(update_fields=['last_idle_started', 'updated_at'])
    except ActivitySession.DoesNotExist:
        logger.error(
            f"ActivitySession not found during idle start: {activity_session_id}"
        )

    return activity_services.log_idle_period(
        activity_session_id=activity_session_id,
        idle_type=data.get('idleType', 'no_input'),
        started_at=started_at,
        ended_at=data.get('endedAt'),
        duration_seconds=data.get('durationSeconds', 0),
        last_active_app=last_app,
        last_active_domain=data.get('lastActiveDomain', ''),
    )


def _create_pending_disappearance(activity_session, idle_period):
    """
    Create a pending Disappearance record from a closed idle period.

    Called automatically when an idle period ends (user returns from idle).
    The Disappearance starts with explanation_status='pending' and waits
    for the user to explain it on the dashboard or before Stop My Day.

    Args:
        activity_session (ActivitySession): The activity session
        idle_period (IdlePeriod): The closed idle period

    Returns:
        Disappearance or None: Created record, or None on failure
    """
    try:
        session = activity_session.session
        dis = Disappearance.objects.create(
            session=session,
            disappearance_type='other',
            custom_location='',
            ai_response='',
            explanation_status='pending',
            reason_source='auto_generated',
            idle_duration_seconds=idle_period.duration_seconds,
            last_active_app=idle_period.last_active_app or '',
            last_window_title='',
        )
        return dis
    except Exception as e:
        logger.error(f"Failed to create pending Disappearance: {e}", exc_info=True)
        return None


def process_idle_end(data):
    """
    Process an idle-end event (user resumed activity).

    Updates the open IdlePeriod with end time and duration.

    Args:
        data (dict): {
            activitySessionId (str): ActivitySession UUID,
            endedAt (str): ISO timestamp when activity resumed,
            durationSeconds (float): Actual idle duration,
        }

    Returns:
        dict: {
            'success': bool,
            'data': {
                'idlePeriodId': str,
                'durationSeconds': float,
            }
        }
    """
    activity_session_id = data.get('activitySessionId')
    if not activity_session_id:
        return {'success': False, 'error': 'activitySessionId required'}

    ended_at = data.get('endedAt', timezone.now().isoformat())
    duration = data.get('durationSeconds', 0)

    # Find the most recent open idle period for this session
    from .models import IdlePeriod
    try:
        act_session = ActivitySession.objects.get(id=activity_session_id)
        open_idle = act_session.idle_periods.filter(ended_at__isnull=True).order_by('-started_at').first()

        if open_idle:
            if isinstance(ended_at, str):
                ended_dt = parse_datetime(ended_at) or timezone.now()
            else:
                ended_dt = ended_at
            open_idle.ended_at = ended_dt
            # Prefer server-computed duration from timestamps to prevent
            # client-supplied inflation. Fall back to client value only
            # if timestamps are unavailable.
            computed_duration = (ended_dt - open_idle.started_at).total_seconds()
            open_idle.duration_seconds = computed_duration if computed_duration > 0 else duration
            open_idle.save()

            # Update totals
            act_session.total_idle_seconds += open_idle.duration_seconds
            act_session.last_idle_started = None
            act_session.save(update_fields=[
                'total_idle_seconds', 'last_idle_started', 'updated_at'
            ])

            # Auto-create pending Disappearance from this idle period
            pending = _create_pending_disappearance(act_session, open_idle)

            return {
                'success': True,
                'data': {
                    'idlePeriodId': str(open_idle.id),
                    'durationSeconds': open_idle.duration_seconds,
                    'pendingDisappearanceId': str(pending.id) if pending else None,
                }
            }
        else:
            return {'success': False, 'error': 'No open idle period found'}

    except ActivitySession.DoesNotExist:
        return {'success': False, 'error': 'Activity session not found'}


def process_end_session(data):
    """
    Process a desktop agent end-session request.

    Closes any open idle periods, finalizes totals, ends the session.

    Args:
        data (dict): {
            activitySessionId (str): ActivitySession UUID
        }

    Returns:
        dict: Result from activity_services.end_activity_session
    """
    activity_session_id = data.get('activitySessionId')
    if not activity_session_id:
        return {'success': False, 'error': 'activitySessionId required'}

    # Auto-close any open idle periods and create pending Disappearances
    from .models import IdlePeriod
    try:
        act_session = ActivitySession.objects.get(id=activity_session_id)
        now = timezone.now()
        open_idles = act_session.idle_periods.filter(ended_at__isnull=True)
        for idle in open_idles:
            idle.ended_at = now
            idle.duration_seconds = (now - idle.started_at).total_seconds()
            idle.save()
            act_session.total_idle_seconds += idle.duration_seconds
            # Create pending Disappearance for each auto-closed idle period
            _create_pending_disappearance(act_session, idle)
        act_session.last_idle_started = None
        act_session.save(update_fields=['total_idle_seconds', 'last_idle_started', 'updated_at'])
    except ActivitySession.DoesNotExist:
        logger.error(
            f"ActivitySession not found during end session cleanup: {activity_session_id}"
        )

    return activity_services.end_activity_session(activity_session_id)


# ============================================================
# DESKTOP AGENT STATUS / HEALTH
# ============================================================

def get_agent_status(session_id):
    """
    Get the current status of the desktop agent for a session.

    Returns info about whether an agent is connected, what app is active,
    idle state, and event stats.

    Args:
        session_id (str/UUID): Parent Session ID

    Returns:
        dict: {
            'agentConnected': bool,
            'activeApp': str,
            'isIdle': bool,
            'idleSince': str or None,
            'eventCount': int,
            'focusChanges': int,
            'activeSeconds': float,
            'idleSeconds': float,
        }
    """
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return {
            'agentConnected': False,
            'activeApp': '',
            'isIdle': False,
            'idleSince': None,
            'eventCount': 0,
            'focusChanges': 0,
            'activeSeconds': 0,
            'idleSeconds': 0,
        }

    # Find active activity session
    active_session = session.activity_sessions.filter(is_active=True).first()

    if not active_session:
        return {
            'agentConnected': False,
            'activeApp': '',
            'isIdle': False,
            'idleSince': None,
            'eventCount': 0,
            'focusChanges': 0,
            'activeSeconds': 0,
            'idleSeconds': 0,
        }

    return {
        'agentConnected': True,
        'activeApp': active_session.last_active_app,
        'isIdle': active_session.last_idle_started is not None,
        'idleSince': (
            active_session.last_idle_started.isoformat()
            if active_session.last_idle_started else None
        ),
        'eventCount': active_session.event_count,
        'focusChanges': active_session.focus_change_count,
        'activeSeconds': active_session.total_active_seconds,
        'idleSeconds': active_session.total_idle_seconds,
    }

