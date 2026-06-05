"""
ProcrastinaAI Tests — Activity Tracking
Tests event logging, batch events, focus switches, and event count accuracy.
"""

import json
from django.test import TestCase, Client
from procrastina_ai.models import Session, ActivitySession, ActivityLog, ApplicationUsage


class ActivityTrackingTest(TestCase):
    """Tests for activity event logging from the desktop agent."""

    def setUp(self):
        self.client = Client()
        self.base = '/projects/procrastina-ai/api'
        # Create parent session
        resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps({
                'mood': 'motivated',
                'interests': ['AI', 'Coding'],
                'tasks': ['Build feature', 'Write tests'],
            }),
            content_type='application/json',
        )
        self.session_id = resp.json()['data']['sessionId']

        # Start agent activity session
        start_resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
                'clientVersion': '1.0.0',
                'platform': 'windows',
            }),
            content_type='application/json',
        )
        self.act_session_id = start_resp.json()['data']['activitySessionId']

    # ------------------------------------------------------------------
    # Single Event Logging
    # ------------------------------------------------------------------

    def test_log_single_event(self):
        """POST activity/log with app_focus should create ActivityLog + ApplicationUsage."""
        resp = self.client.post(
            f'{self.base}/activity/log/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'eventType': 'app_focus',
                'targetName': 'code.exe',
                'windowTitle': 'main.py — project',
                'durationSeconds': 120,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        # Normalized name should be returned
        self.assertEqual(data['data']['targetName'], 'Visual Studio Code')

        # Verify ActivityLog
        logs = ActivityLog.objects.filter(activity_session_id=self.act_session_id)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().event_type, 'app_focus')

        # Verify ApplicationUsage
        usage = ApplicationUsage.objects.filter(activity_session_id=self.act_session_id)
        self.assertEqual(usage.count(), 1)
        self.assertEqual(usage.first().app_name, 'Visual Studio Code')
        self.assertEqual(usage.first().total_seconds, 120)

    def test_log_event_missing_target(self):
        """app_focus without targetName should fail validation."""
        resp = self.client.post(
            f'{self.base}/activity/log/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'eventType': 'app_focus',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Batch Events
    # ------------------------------------------------------------------

    def test_log_batch_events(self):
        """POST batch of 5 events should log all of them."""
        events = [
            {'eventType': 'app_focus', 'targetName': 'code.exe', 'durationSeconds': 60},
            {'eventType': 'app_focus', 'targetName': 'chrome.exe', 'durationSeconds': 30},
            {'eventType': 'input_detected', 'targetName': 'keyboard'},
            {'eventType': 'app_focus', 'targetName': 'discord.exe', 'durationSeconds': 45},
            {'eventType': 'window_change', 'targetName': 'code.exe'},
        ]
        resp = self.client.post(
            f'{self.base}/activity/log/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'events': events,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['loggedCount'], 5)

        # Verify all events are stored
        logs = ActivityLog.objects.filter(activity_session_id=self.act_session_id)
        self.assertEqual(logs.count(), 5)

    # ------------------------------------------------------------------
    # Focus Switch Detection
    # ------------------------------------------------------------------

    def test_focus_switch_detection(self):
        """Logging focus on app A then app B should increment focus_change_count."""
        # Focus app A
        self.client.post(
            f'{self.base}/activity/log/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'eventType': 'app_focus',
                'targetName': 'code.exe',
                'durationSeconds': 60,
            }),
            content_type='application/json',
        )

        # Focus app B (should trigger focus change)
        resp = self.client.post(
            f'{self.base}/activity/log/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'eventType': 'app_focus',
                'targetName': 'chrome.exe',
                'durationSeconds': 30,
            }),
            content_type='application/json',
        )
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['focusChanged'])

        # Check activity session focus_change_count
        act_session = ActivitySession.objects.get(id=self.act_session_id)
        self.assertEqual(act_session.focus_change_count, 1)
        self.assertEqual(act_session.last_active_app, 'Google Chrome')

    # ------------------------------------------------------------------
    # Event Count Accuracy
    # ------------------------------------------------------------------

    def test_event_count_accuracy(self):
        """event_count on ActivitySession should match actual logged events."""
        # Log 3 events individually
        for name in ['code.exe', 'chrome.exe', 'discord.exe']:
            self.client.post(
                f'{self.base}/activity/log/',
                data=json.dumps({
                    'activitySessionId': self.act_session_id,
                    'eventType': 'app_focus',
                    'targetName': name,
                }),
                content_type='application/json',
            )

        act_session = ActivitySession.objects.get(id=self.act_session_id)
        self.assertEqual(act_session.event_count, 3)

        # Verify against actual event count
        actual_count = ActivityLog.objects.filter(
            activity_session_id=self.act_session_id
        ).count()
        self.assertEqual(act_session.event_count, actual_count)

    # ------------------------------------------------------------------
    # No Duplicate Events
    # ------------------------------------------------------------------

    def test_no_duplicate_events(self):
        """Each POST should create exactly one event — no retries or duplicates."""
        payload = json.dumps({
            'activitySessionId': self.act_session_id,
            'eventType': 'app_focus',
            'targetName': 'code.exe',
            'durationSeconds': 60,
        })

        # Send same payload twice — should create 2 separate events
        self.client.post(
            f'{self.base}/activity/log/',
            data=payload,
            content_type='application/json',
        )
        self.client.post(
            f'{self.base}/activity/log/',
            data=payload,
            content_type='application/json',
        )

        logs = ActivityLog.objects.filter(activity_session_id=self.act_session_id)
        self.assertEqual(logs.count(), 2)

        act_session = ActivitySession.objects.get(id=self.act_session_id)
        self.assertEqual(act_session.event_count, 2)
