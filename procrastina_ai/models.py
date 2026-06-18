from django.db import models
import uuid


class Session(models.Model):
    """
    Stores user session data including mood, interests, and tasks.
    Each session represents a single procrastination tracking session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User profile data
    mood = models.CharField(
        max_length=50,
        choices=[
            ('motivated', 'Motivated'),
            ('sleepy', 'Sleepy'),
            ('burned_out', 'Burned Out'),
            ('lazy', 'Lazy'),
            ('existential_crisis', 'Existential Crisis'),
        ],
        help_text="User's current mood"
    )
    interests = models.JSONField(
        default=list,
        help_text="List of user interests (YouTube, AI, Gaming, etc.)"
    )
    tasks = models.JSONField(
        default=list,
        help_text="List of tasks user planned to do"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Session status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the session is currently active (ended via 'Stop My Day')"
    )
    
    # Activity tracking (real browser activity, not estimated)
    active_seconds = models.FloatField(
        default=0,
        help_text="Total seconds of detected browser activity (mousemove, click, keydown, scroll)"
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when session was ended via 'Stop My Day'"
    )
    activity_data_sufficient = models.BooleanField(
        default=False,
        help_text="Whether enough activity data was collected for accurate reporting"
    )

    # Task completion review (filled during Stop My Day flow)
    task_statuses = models.JSONField(
        default=dict,
        help_text="Task completion statuses: {task_name: {status, completion_score}}"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
    
    def __str__(self):
        return f"Session {self.id} - {self.mood}"


class Disappearance(models.Model):
    """
    Tracks where user "disappeared" to during their procrastination session.
    Stores the type of disappearance and AI-generated response.

    EXPLANATION WORKFLOW:
      - When idle period ends (user returns), a Disappearance is auto-created
        with explanation_status='pending'.
      - User can explain it later (dashboard) or before Stop My Day.
      - 'explained' = user provided a reason, 'unexplained' = user skipped.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key to session
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='disappearances',
        help_text="Session this disappearance belongs to"
    )
    
    # Disappearance data
    disappearance_type = models.CharField(
        max_length=100,
        choices=[
            ('youtube', 'Watching YouTube'),
            ('laptops', 'Looking At Laptops'),
            ('ai_tools', 'Researching AI Tools'),
            ('startup', 'Planning A Startup'),
            ('comments', 'Reading Comments'),
            ('other', 'Other (custom location)'),
        ],
        default='other',
        help_text="Where the user disappeared to"
    )
    custom_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom location if 'other' was selected"
    )
    
    # AI response
    ai_response = models.TextField(
        blank=True,
        help_text="AI-generated witty response about the disappearance"
    )

    # ============================================================
    # PENDING EXPLANATION QUEUE
    # ============================================================
    EXPLANATION_STATUS_CHOICES = [
        ('pending', 'Pending Explanation'),
        ('explained', 'Explained by User'),
        ('unexplained', 'User Chose to Remain a Mystery'),
    ]
    explanation_status = models.CharField(
        max_length=20,
        choices=EXPLANATION_STATUS_CHOICES,
        default='pending',
        help_text="Whether user has explained this disappearance"
    )

    explanation_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user provided the explanation"
    )

    REASON_SOURCE_CHOICES = [
        ('auto_generated', 'Auto-created from idle detection'),
        ('user_selected', 'User picked from preset options'),
        ('custom_text', 'User typed a custom reason'),
    ]
    reason_source = models.CharField(
        max_length=20,
        choices=REASON_SOURCE_CHOICES,
        blank=True,
        default='',
        help_text="How the disappearance reason was determined"
    )

    # Context from the desktop agent (stored when idle ended)
    idle_duration_seconds = models.FloatField(
        default=0,
        help_text="How long the idle period lasted (seconds)"
    )
    last_active_app = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Application focused before this disappearance"
    )
    last_window_title = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Window title before this disappearance"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Disappearance'
        verbose_name_plural = 'Disappearances'
    
    def __str__(self):
        return f"Disappearance - {self.disappearance_type} ({self.explanation_status})"


class Report(models.Model):
    """
    Stores daily procrastination reports with AI-generated summaries and statistics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key to session
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='reports',
        help_text="Session this report belongs to"
    )
    
    # Report statistics
    report_date = models.DateField(
        auto_now_add=True,
        help_text="Date of the report"
    )
    tasks_planned = models.IntegerField(
        default=0,
        help_text="Number of tasks user planned"
    )
    tasks_completed = models.IntegerField(
        default=0,
        help_text="Number of tasks completed"
    )
    total_disappearances = models.IntegerField(
        default=0,
        help_text="Total number of disappearances"
    )
    procrastination_score = models.IntegerField(
        default=0,
        help_text="Procrastination score (0-100)"
    )
    
    # AI-generated content
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated procrastination report summary"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-report_date']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
    
    def __str__(self):
        return f"Report - {self.report_date}"


class Prediction(models.Model):
    """
    Stores the AI-generated procrastination forecast for a session.

    The prediction simulates the user's entire workday as a humorous
    'weather forecast for procrastination', including journey steps
    with durations, natural breaks, and forecast metrics.

    Used later by reports to compare predicted vs actual day.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to the session this prediction was generated for
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='predictions',
        help_text="Session this prediction belongs to"
    )

    # Forecast headline (e.g. "High chance of AI tool exploration. Moderate chance of productivity.")
    forecast_summary = models.TextField(
        blank=True,
        help_text="AI-generated forecast headline"
    )

    # Journey steps with durations, distraction risk, recovery chance
    # Format: [{"title": "...", "duration": "25 min", "distractionRisk": "Low", "recoveryChance": "High", "icon": "..."}]
    journey = models.JSONField(
        default=list,
        help_text="Full-day journey steps with durations and probabilities"
    )

    # Natural breaks (coffee, lunch, etc.)
    # Format: [{"title": "Coffee Mission", "duration": "10-20 Minutes", "icon": "\u2615"}]
    natural_breaks = models.JSONField(
        default=list,
        help_text="AI-generated natural workday breaks"
    )

    # Forecast metrics
    # Format: {"productivity": 68, "distraction": 83, "completion": 21, "mainDistraction": "AI Tools"}
    metrics = models.JSONField(
        default=dict,
        help_text="Predicted productivity, distraction, completion scores and main distraction"
    )

    # AI warnings
    # Format: ["Today's plan contains 4 tasks...", "The AI is strangely confident..."]
    warnings = models.JSONField(
        default=list,
        help_text="AI-generated warning messages"
    )

    # Prediction confidence (0-100)
    confidence = models.IntegerField(
        default=94,
        help_text="How confident the AI is about this prediction"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prediction'
        verbose_name_plural = 'Predictions'

    def __str__(self):
        return f"Prediction - {self.session_id} ({self.created_at.date()})"


# ============================================================
# DESKTOP ACTIVITY TRACKING MODELS
# ============================================================
# These models support future integration with:
#   - Python Desktop Agent (pystray, psutil, pywinauto)
#   - Browser Extension (chrome.tabs, chrome.history APIs)
#
# Current system uses MANUAL distraction logging (Session/Disappearance).
# These models add AUTOMATED activity detection without changing
# the existing manual workflow.
#
# Architecture:
#   Session (existing manual session)
#     └── ActivitySession (desktop/browser tracking session)
#           ├── ActivityLog (individual events)
#           ├── ApplicationUsage (app time aggregation)
#           ├── WebsiteUsage (website time aggregation)
#           └── IdlePeriod (detected idle windows)
# ============================================================


class ActivitySession(models.Model):
    """
    Represents a desktop/browser activity tracking session.
    Linked to the main Session (manual workflow).

    Future data sources:
    - Python Desktop Agent: monitors active window, keyboard/mouse activity
    - Browser Extension: monitors tab activity, website visits

    An ActivitySession starts when the desktop agent or browser extension
    connects and stops when it disconnects or the user ends the day.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to the main manual session
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='activity_sessions',
        help_text="Parent manual session"
    )

    # Source of this activity data
    SOURCE_CHOICES = [
        ('desktop_agent', 'Python Desktop Agent'),
        ('browser_extension', 'Browser Extension'),
        ('mobile_app', 'Mobile App'),
        ('manual_api', 'Manual API (testing)'),
    ]
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        help_text="What sent this activity data"
    )

    # Client metadata (for debugging and analytics)
    client_version = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Version of the desktop agent or browser extension"
    )
    platform = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="OS platform: windows, macos, linux"
    )

    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When tracking started"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last activity event received"
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When tracking ended"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this activity session is still running"
    )

    # Aggregated totals (updated periodically by the service layer)
    total_active_seconds = models.FloatField(
        default=0,
        help_text="Total seconds of active usage across all apps/websites"
    )
    total_idle_seconds = models.FloatField(
        default=0,
        help_text="Total seconds of detected idle time"
    )

    # Raw event count (for analytics)
    event_count = models.IntegerField(
        default=0,
        help_text="Total number of activity events received"
    )

    # Focus tracking stats
    focus_change_count = models.IntegerField(
        default=0,
        help_text="Number of application focus switches detected"
    )
    last_active_app = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Currently or most recently focused application"
    )
    last_idle_started = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When current idle period started (null if not idle)"
    )

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Activity Session'
        verbose_name_plural = 'Activity Sessions'

    def __str__(self):
        return f"ActivitySession {self.id} ({self.source}) - Session {self.session_id}"


class ActivityLog(models.Model):
    """
    Individual activity event from a desktop agent or browser extension.

    Event types:
    - app_focus: User switched to an application (VS Code, Chrome, etc.)
    - app_blur: User left an application
    - website_visit: User visited a website (from browser extension)
    - website_leave: User left a website
    - input_detected: Keyboard or mouse activity burst
    - window_change: Active window changed

    This is the raw event stream. ApplicationUsage and WebsiteUsage
    aggregate these events into readable summaries.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to activity session
    activity_session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="Activity session this event belongs to"
    )

    # Event classification
    EVENT_TYPES = [
        ('app_focus', 'Application Focused'),
        ('app_blur', 'Application Blurred'),
        ('website_visit', 'Website Visited'),
        ('website_leave', 'Website Left'),
        ('input_detected', 'Input Activity Detected'),
        ('window_change', 'Window Changed'),
        ('system_event', 'System Event (lock, sleep, etc.)'),
    ]
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        help_text="Type of activity event"
    )

    # What the user was doing
    # For app_focus: application name (e.g., 'Visual Studio Code', 'Chrome')
    # For website_visit: domain or URL (e.g., 'youtube.com', 'instagram.com')
    target_name = models.CharField(
        max_length=255,
        help_text="Application name or website domain"
    )

    # Optional category for grouping
    # e.g., 'productivity', 'social', 'entertainment', 'development', 'ai_tools'
    CATEGORY_CHOICES = [
        ('productivity', 'Productivity (VS Code, Notion, etc.)'),
        ('development', 'Development (IDE, Terminal, Git)'),
        ('communication', 'Communication (Slack, Email, Discord)'),
        ('social', 'Social Media (Instagram, Twitter, Reddit)'),
        ('entertainment', 'Entertainment (YouTube, Netflix, Gaming)'),
        ('ai_tools', 'AI Tools (ChatGPT, Claude, etc.)'),
        ('browsing', 'General Browsing'),
        ('system', 'System (Desktop, File Explorer)'),
        ('other', 'Other'),
    ]
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Category of the target application/website"
    )

    # Extra metadata (JSON for flexibility)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra data: window title, URL path, process name, etc."
    )

    # Timing
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this event occurred"
    )
    duration_seconds = models.FloatField(
        default=0,
        help_text="How long this event lasted (if applicable)"
    )

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['activity_session', 'event_type']),
            models.Index(fields=['target_name', 'category']),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.target_name} ({self.category})"


class ApplicationUsage(models.Model):
    """
    Aggregated time spent in a specific application.
    Built from ActivityLog events by the activity processing service.

    Examples:
    - VS Code: 45 minutes
    - Chrome: 2 hours 10 minutes
    - Slack: 15 minutes

    Used in reports to show where time actually went.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to activity session
    activity_session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        related_name='application_usage',
        help_text="Activity session this usage belongs to"
    )

    # Application info
    app_name = models.CharField(
        max_length=255,
        help_text="Application name (e.g., 'Visual Studio Code', 'Chrome')"
    )
    app_process = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Process name (e.g., 'code.exe', 'chrome.exe')"
    )

    # Category (mirrors ActivityLog categories)
    category = models.CharField(
        max_length=30,
        choices=ActivityLog.CATEGORY_CHOICES,
        default='other',
        help_text="Category of this application"
    )

    # Time tracking
    total_seconds = models.FloatField(
        default=0,
        help_text="Total time spent in this application (seconds)"
    )
    focus_events = models.IntegerField(
        default=0,
        help_text="Number of times user focused this app"
    )

    # First/last seen
    first_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="First time this app was focused"
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this app was focused"
    )

    class Meta:
        ordering = ['-total_seconds']
        verbose_name = 'Application Usage'
        verbose_name_plural = 'Application Usages'
        unique_together = ['activity_session', 'app_name']

    def __str__(self):
        return f"{self.app_name}: {self.total_seconds}s"


class WebsiteUsage(models.Model):
    """
    Aggregated time spent on a specific website or domain.
    Built from browser extension data or ActivityLog events.

    Examples:
    - youtube.com: 1 hour 30 minutes
    - instagram.com: 25 minutes
    - chat.openai.com: 40 minutes

    Used in reports to show which websites consumed the most time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to activity session
    activity_session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        related_name='website_usage',
        help_text="Activity session this usage belongs to"
    )

    # Website info
    domain = models.CharField(
        max_length=255,
        help_text="Website domain (e.g., 'youtube.com', 'instagram.com')"
    )
    title = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Page title (e.g., 'Cat videos - YouTube')"
    )
    url_path = models.CharField(
        max_length=1000,
        blank=True,
        default='',
        help_text="URL path for deeper tracking (e.g., '/watch?v=...')"
    )

    # Category (mirrors ActivityLog categories)
    category = models.CharField(
        max_length=30,
        choices=ActivityLog.CATEGORY_CHOICES,
        default='browsing',
        help_text="Category of this website"
    )

    # Time tracking
    total_seconds = models.FloatField(
        default=0,
        help_text="Total time spent on this domain (seconds)"
    )
    visit_count = models.IntegerField(
        default=0,
        help_text="Number of visits to this domain"
    )

    # First/last seen
    first_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="First time this site was visited"
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this site was visited"
    )

    class Meta:
        ordering = ['-total_seconds']
        verbose_name = 'Website Usage'
        verbose_name_plural = 'Website Usages'
        unique_together = ['activity_session', 'domain']

    def __str__(self):
        return f"{self.domain}: {self.total_seconds}s ({self.visit_count} visits)"


class IdlePeriod(models.Model):
    """
    Detected period of no user activity.
    Created by the desktop agent when no keyboard/mouse input is detected
    for a configurable threshold (default: 5 minutes).

    Used to separate active time from idle time in reports.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to activity session
    activity_session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        related_name='idle_periods',
        help_text="Activity session this idle period belongs to"
    )

    # Idle detection
    IDLE_TYPES = [
        ('no_input', 'No keyboard/mouse input'),
        ('screen_locked', 'Screen locked'),
        ('system_sleep', 'System sleep/hibernate'),
        ('away', 'User away (manual)'),
    ]
    idle_type = models.CharField(
        max_length=20,
        choices=IDLE_TYPES,
        default='no_input',
        help_text="Reason this period was classified as idle"
    )

    # Timing
    started_at = models.DateTimeField(
        help_text="When idle period started"
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When idle period ended (null if still idle)"
    )
    duration_seconds = models.FloatField(
        default=0,
        help_text="Total duration of idle period in seconds"
    )

    # What was active before going idle (context)
    last_active_app = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Application that was focused before idle started"
    )
    last_active_domain = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Website that was active before idle started"
    )

    class Meta:
        ordering = ['started_at']
        verbose_name = 'Idle Period'
        verbose_name_plural = 'Idle Periods'

    def __str__(self):
        return f"Idle ({self.idle_type}): {self.duration_seconds}s"
