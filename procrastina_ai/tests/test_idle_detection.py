"""
ProcrastinaAI Tests — Idle Detection
Tests idle period creation, ending, auto-close on session end,
and total idle time accumulation.
"""

import json
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from procrastina_ai.models import Session, ActivitySession, IdlePeriod


class IdleDetectionTest(TestCase):
    """Tests for idle period logging and management."""

    def setUp(self):
        self.client = Client()
        self.base = '/projects/procrastina-ai/api'
        # Create parent session
        resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps({
                'mood': 'sleepy',
                'interests': ['YouTube'],
                'tasks': ['Write blog post'],
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
            }),
            content_type='application/json',
        )
        self.act_session_id = start_resp.json()['data']['activitySessionId']

    # ------------------------------------------------------------------
    # Idle Start
    # ------------------------------------------------------------------

    def test_idle_start(self):
        """POST activity/idle should create an IdlePeriod."""
        now = timezone.now()
        resp = self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'idleType': 'no_input',
                'startedAt': now.isoformat(),
                'lastActiveApp': 'Visual Studio Code',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('idlePeriodId', data['data'])

        # Verify DB
        idle = IdlePeriod.objects.get(id=data['data']['idlePeriodId'])
        self.assertEqual(idle.idle_type, 'no_input')
        self.assertIsNone(idle.ended_at)
        self.assertEqual(idle.last_active_app, 'Visual Studio Code')

    def test_idle_start_missing_fields(self):
        """Idle start without required fields should fail."""
        resp = self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Idle End
    # ------------------------------------------------------------------

    def test_idle_end(self):
        """POST activity/idle-end should close the open IdlePeriod."""
        now = timezone.now()
        # Start idle
        start_resp = self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'idleType': 'no_input',
                'startedAt': (now - timedelta(minutes=10)).isoformat(),
                'durationSeconds': 0,
            }),
            content_type='application/json',
        )
        idle_id = start_resp.json()['data']['idlePeriodId']

        # End idle
        resp = self.client.post(
            f'{self.base}/activity/idle-end/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'endedAt': now.isoformat(),
                'durationSeconds': 600,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['durationSeconds'], 600)

        # Verify idle period is closed
        idle = IdlePeriod.objects.get(id=idle_id)
        self.assertIsNotNone(idle.ended_at)
        self.assertEqual(idle.duration_seconds, 600)

    def test_idle_end_no_open_period(self):
        """Ending idle when no open period exists should fail."""
        resp = self.client.post(
            f'{self.base}/activity/idle-end/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'endedAt': timezone.now().isoformat(),
                'durationSeconds': 100,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    # ------------------------------------------------------------------
    # Auto-Close on Session End
    # ------------------------------------------------------------------

    def test_auto_close_on_session_end(self):
        """Ending the activity session should auto-close any open idle period."""
        now = timezone.now()
        # Start idle
        self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'idleType': 'no_input',
                'startedAt': (now - timedelta(minutes=5)).isoformat(),
            }),
            content_type='application/json',
        )

        # End activity session (should auto-close idle)
        self.client.post(
            f'{self.base}/activity/end-session/',
            data=json.dumps({'activitySessionId': self.act_session_id}),
            content_type='application/json',
        )

        # Verify idle period was auto-closed
        idle = IdlePeriod.objects.filter(activity_session_id=self.act_session_id).first()
        self.assertIsNotNone(idle)
        self.assertIsNotNone(idle.ended_at)
        self.assertGreater(idle.duration_seconds, 0)

    # ------------------------------------------------------------------
    # Total Idle Accumulation
    # ------------------------------------------------------------------

    def test_total_idle_accumulation(self):
        """Multiple idle periods should accumulate total_idle_seconds correctly."""
        now = timezone.now()

        # First idle: started 300s ago, ended now → 300 seconds
        first_start = now - timedelta(seconds=300)
        self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'idleType': 'no_input',
                'startedAt': first_start.isoformat(),
                'durationSeconds': 0,
            }),
            content_type='application/json',
        )
        # End first idle — server computes 300s from timestamps
        self.client.post(
            f'{self.base}/activity/idle-end/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'endedAt': now.isoformat(),
                'durationSeconds': 300,
            }),
            content_type='application/json',
        )

        # Second idle: started 180s ago, ended now → 180 seconds
        second_start = now - timedelta(seconds=180)
        self.client.post(
            f'{self.base}/activity/idle/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'idleType': 'screen_locked',
                'startedAt': second_start.isoformat(),
                'durationSeconds': 0,
            }),
            content_type='application/json',
        )
        # End second idle — server computes 180s from timestamps
        self.client.post(
            f'{self.base}/activity/idle-end/',
            data=json.dumps({
                'activitySessionId': self.act_session_id,
                'endedAt': now.isoformat(),
                'durationSeconds': 180,
            }),
            content_type='application/json',
        )

        # Check total idle seconds on activity session
        act_session = ActivitySession.objects.get(id=self.act_session_id)
        self.assertEqual(act_session.total_idle_seconds, 480)  # 300 + 180

        # Verify idle period count
        idle_count = IdlePeriod.objects.filter(
            activity_session_id=self.act_session_id
        ).count()
        self.assertEqual(idle_count, 2)
