"""
ProcrastinaAI Django Admin Configuration

Register models for admin panel so admins can view:
- User sessions
- Disappearances
- Daily reports
"""

from django.contrib import admin
from .models import (
    Session, Disappearance, Report, Prediction,
    ActivitySession, ActivityLog, ApplicationUsage,
    WebsiteUsage, IdlePeriod,
)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """
    Admin interface for Session model.
    Allows viewing and filtering user sessions.
    """
    list_display = ['id', 'mood', 'created_at', 'disappearances_count']
    list_filter = ['mood', 'created_at']
    search_fields = ['id', 'interests']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def disappearances_count(self, obj):
        """Display count of disappearances for this session."""
        return obj.disappearances.count()
    disappearances_count.short_description = 'Disappearances'


@admin.register(Disappearance)
class DisappearanceAdmin(admin.ModelAdmin):
    """
    Admin interface for Disappearance model.
    Allows viewing where users went during procrastination.
    """
    list_display = ['id', 'session', 'disappearance_type', 'created_at']
    list_filter = ['disappearance_type', 'created_at', 'session']
    search_fields = ['id', 'session__id', 'custom_location']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('id', 'session', 'created_at')
        }),
        ('Disappearance Details', {
            'fields': ('disappearance_type', 'custom_location')
        }),
        ('AI Response', {
            'fields': ('ai_response',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin interface for Report model.
    Allows viewing daily procrastination reports.
    """
    list_display = ['id', 'session', 'report_date', 'procrastination_score', 'tasks_completed']
    list_filter = ['report_date', 'procrastination_score', 'session']
    search_fields = ['id', 'session__id']
    readonly_fields = ['id', 'created_at', 'report_date']
    
    fieldsets = (
        ('Report Info', {
            'fields': ('id', 'session', 'report_date', 'created_at')
        }),
        ('Statistics', {
            'fields': ('tasks_planned', 'tasks_completed', 'total_disappearances', 'procrastination_score')
        }),
        ('AI Summary', {
            'fields': ('ai_summary',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    """
    Admin interface for Prediction model.
    Stores the full-day procrastination forecast for each session.
    """
    list_display = ['id', 'session', 'confidence', 'created_at']
    list_filter = ['confidence', 'created_at']
    search_fields = ['id', 'session__id']
    readonly_fields = ['id', 'created_at']


# ============================================================
# Activity Tracking Models (Desktop Agent)
# ============================================================

@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'source', 'is_active', 'event_count', 'focus_change_count']
    list_filter = ['source', 'is_active']
    search_fields = ['id', 'session__id']
    readonly_fields = ['id', 'started_at', 'ended_at', 'updated_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'activity_session', 'event_type', 'target_name', 'category', 'duration_seconds']
    list_filter = ['event_type', 'category']
    search_fields = ['id', 'target_name']
    readonly_fields = ['id']


@admin.register(ApplicationUsage)
class ApplicationUsageAdmin(admin.ModelAdmin):
    list_display = ['id', 'activity_session', 'app_name', 'category', 'total_seconds', 'focus_events']
    list_filter = ['category']
    search_fields = ['app_name']
    readonly_fields = ['id']


@admin.register(WebsiteUsage)
class WebsiteUsageAdmin(admin.ModelAdmin):
    list_display = ['id', 'activity_session', 'domain', 'category', 'total_seconds', 'visit_count']
    list_filter = ['category']
    search_fields = ['domain']
    readonly_fields = ['id']


@admin.register(IdlePeriod)
class IdlePeriodAdmin(admin.ModelAdmin):
    list_display = ['id', 'activity_session', 'idle_type', 'duration_seconds', 'last_active_app']
    list_filter = ['idle_type']
    search_fields = ['id', 'last_active_app']
    readonly_fields = ['id']

