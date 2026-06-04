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
    path('where-did-you-go/', views.disappearance, name='disappearance'),

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
]

