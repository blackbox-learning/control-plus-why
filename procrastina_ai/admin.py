"""
ProcrastinaAI Django Admin Configuration

Register models for admin panel so admins can view:
- User sessions
- Disappearances
- Daily reports
"""

from django.contrib import admin
from .models import Session, Disappearance, Report


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

