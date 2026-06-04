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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Disappearance'
        verbose_name_plural = 'Disappearances'
    
    def __str__(self):
        return f"Disappearance - {self.disappearance_type}"


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
