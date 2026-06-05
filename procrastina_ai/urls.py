"""
ProcrastinaAI URL Configuration

Routes are organized as:
- Page views: Render HTML templates (regular URLs)
- API views: Return JSON responses (api/ prefix)

All URLs are namespaced under 'procrastina_ai'.
"""

from django.urls import path
from . import views

app_name = 'procrastina_ai'

urlpatterns = [
    # ============================================================
    # Page Views - Render HTML Templates
    # ============================================================
    path('', views.index, name='index'),
    path('setup/', views.setup, name='setup'),
    path('prediction/', views.prediction, name='prediction'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('report/', views.report, name='report'),
    path('funny-reasons/', views.funny_reasons, name='funny_reasons'),

    # ============================================================
    # API Views - Return JSON Responses
    # ============================================================
    # All API endpoints are prefixed with 'api/' for clarity
    
    # POST /projects/procrastina-ai/api/create-session/
    # Create a new user session
    path('api/create-session/', views.api_create_session, name='api_create_session'),
    
    # POST /projects/procrastina-ai/api/generate-prediction/
    # Generate AI procrastination prediction
    path('api/generate-prediction/', views.api_generate_prediction, name='api_generate_prediction'),
    
    # POST /projects/procrastina-ai/api/save-disappearance/
    # Save where user disappeared + get AI response
    path('api/save-disappearance/', views.api_save_disappearance, name='api_save_disappearance'),
    
    # POST /projects/procrastina-ai/api/generate-report/
    # Generate daily procrastination report
    path('api/generate-report/', views.api_generate_report, name='api_generate_report'),
    
    # POST /projects/procrastina-ai/api/generate-funny-reasons/
    # Generate funny reasons for a task
    path('api/generate-funny-reasons/', views.api_generate_funny_reasons, name='api_generate_funny_reasons'),

    # GET /projects/procrastina-ai/api/session-data/?sessionId=xxx
    # Get full session data + disappearances + reports
    path('api/session-data/', views.api_get_session_data, name='api_get_session_data'),
    
    # POST /projects/procrastina-ai/api/end-session/
    # End active session ('Stop My Day')
    path('api/end-session/', views.api_end_session, name='api_end_session'),

    # POST /projects/procrastina-ai/api/activity-heartbeat/
    # Receive activity tracking heartbeat from client
    path('api/activity-heartbeat/', views.api_activity_heartbeat, name='api_activity_heartbeat'),

    # ============================================================
    # IDLE RETURN + SESSION RECOVERY + AGENT MANAGEMENT
    # ============================================================

    # GET /projects/procrastina-ai/api/idle-return-options/?sessionId=xxx
    # Get contextual distraction options for idle-return popup
    path('api/idle-return-options/', views.api_idle_return_options, name='api_idle_return_options'),

    # POST /projects/procrastina-ai/api/save-return-reason/
    # Save idle-return reason as Disappearance + get AI reaction
    path('api/save-return-reason/', views.api_save_return_reason, name='api_save_return_reason'),

    # GET /projects/procrastina-ai/api/recover-session/
    # Recover active session after browser/server restart
    path('api/recover-session/', views.api_recover_session, name='api_recover_session'),

    # POST /projects/procrastina-ai/api/agent-disconnect/
    # Force-end active agent ActivitySession during Stop My Day
    path('api/agent-disconnect/', views.api_agent_disconnect, name='api_agent_disconnect'),

    # ============================================================
    # ACTIVITY TRACKING API — Desktop Agent
    # ============================================================
    # These endpoints are used by the Windows desktop agent.
    # All POST endpoints are CSRF-exempt for external client access.
    # ============================================================

    # POST /projects/procrastina-ai/api/activity/start-session/
    # Start a new activity tracking session (linked to manual Session)
    path('api/activity/start-session/', views.api_activity_start_session, name='api_activity_start_session'),

    # POST /projects/procrastina-ai/api/activity/end-session/
    # End an activity tracking session
    path('api/activity/end-session/', views.api_activity_end_session, name='api_activity_end_session'),

    # POST /projects/procrastina-ai/api/activity/log/
    # Log activity event(s) — supports single event or batch
    path('api/activity/log/', views.api_activity_log, name='api_activity_log'),

    # POST /projects/procrastina-ai/api/activity/idle/
    # Log an idle period start (no user activity detected)
    path('api/activity/idle/', views.api_activity_idle, name='api_activity_idle'),

    # POST /projects/procrastina-ai/api/activity/idle-end/
    # End an idle period (user resumed activity)
    path('api/activity/idle-end/', views.api_activity_idle_end, name='api_activity_idle_end'),

    # POST /projects/procrastina-ai/api/activity/report/
    # Generate enhanced report (manual + activity data)
    path('api/activity/report/', views.api_activity_report, name='api_activity_report'),

    # POST /projects/procrastina-ai/api/activity/analytics/
    # Get comprehensive session analytics
    path('api/activity/analytics/', views.api_activity_analytics, name='api_activity_analytics'),
]

