"""
ProcrastinaAI Tests — Agent Connection
Tests the desktop agent activity session lifecycle:
start → log events → end, plus the agent-disconnect endpoint.
"""

import json
from django.test import TestCase, Client
from procrastina_ai.models import Session, ActivitySession


class AgentConnectionTest(TestCase):
    """Tests for desktop agent connection and disconnection."""

    def setUp(self):
        self.client = Client()
        self.base = '/projects/procrastina-ai/api'
        # Create a parent Session first
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

    # ------------------------------------------------------------------
    # Start Activity Session
    # ------------------------------------------------------------------

    def test_start_activity_session(self):
        """POST activity/start-session should create an ActivitySession."""
        resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
                'clientVersion': '1.0.0',
                'platform': 'windows',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('activitySessionId', data['data'])

        # Verify DB record
        act_session = ActivitySession.objects.get(id=data['data']['activitySessionId'])
        self.assertTrue(act_session.is_active)
        self.assertEqual(act_session.source, 'desktop_agent')
        self.assertEqual(str(act_session.session_id), self.session_id)

    def test_start_activity_session_missing_session_id(self):
        """Start session without sessionId should fail."""
        resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({'source': 'desktop_agent'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_start_activity_session_invalid_parent(self):
        """Start session with non-existent parent should fail."""
        import uuid
        resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': str(uuid.uuid4()),
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    # ------------------------------------------------------------------
    # End Activity Session
    # ------------------------------------------------------------------

    def test_end_activity_session(self):
        """POST activity/end-session should mark ActivitySession inactive."""
        # Start
        start_resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        act_session_id = start_resp.json()['data']['activitySessionId']

        # End
        resp = self.client.post(
            f'{self.base}/activity/end-session/',
            data=json.dumps({'activitySessionId': act_session_id}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])

        act_session = ActivitySession.objects.get(id=act_session_id)
        self.assertFalse(act_session.is_active)
        self.assertIsNotNone(act_session.ended_at)

    def test_end_activity_session_not_found(self):
        """End session with invalid ID should fail."""
        import uuid
        resp = self.client.post(
            f'{self.base}/activity/end-session/',
            data=json.dumps({'activitySessionId': str(uuid.uuid4())}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Agent Disconnect Endpoint
    # ------------------------------------------------------------------

    def test_agent_disconnect(self):
        """POST agent-disconnect should end any active agent session."""
        # Start agent session
        start_resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        act_session_id = start_resp.json()['data']['activitySessionId']

        # Disconnect via the management endpoint
        resp = self.client.post(
            f'{self.base}/agent-disconnect/',
            data=json.dumps({'sessionId': self.session_id}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['hadActiveAgent'])

        # Verify agent session is ended
        act_session = ActivitySession.objects.get(id=act_session_id)
        self.assertFalse(act_session.is_active)

    def test_agent_disconnect_no_active(self):
        """Agent disconnect with no active agent should succeed gracefully."""
        resp = self.client.post(
            f'{self.base}/agent-disconnect/',
            data=json.dumps({'sessionId': self.session_id}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['data']['hadActiveAgent'])

    # ------------------------------------------------------------------
    # Duplicate Start
    # ------------------------------------------------------------------

    def test_duplicate_start_creates_new_session(self):
        """Starting a second agent session should create a new ActivitySession."""
        # First start
        resp1 = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        id1 = resp1.json()['data']['activitySessionId']

        # Second start (same parent)
        resp2 = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        id2 = resp2.json()['data']['activitySessionId']

        # Should be different sessions
        self.assertNotEqual(id1, id2)
        self.assertEqual(ActivitySession.objects.filter(session_id=self.session_id).count(), 2)

    # ------------------------------------------------------------------
    # End Session Auto-Ends Agent
    # ------------------------------------------------------------------

    def test_end_session_auto_ends_agent(self):
        """Ending the parent session should auto-end any active agent session."""
        # Start agent
        start_resp = self.client.post(
            f'{self.base}/activity/start-session/',
            data=json.dumps({
                'sessionId': self.session_id,
                'source': 'desktop_agent',
            }),
            content_type='application/json',
        )
        act_session_id = start_resp.json()['data']['activitySessionId']

        # End parent session
        self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': self.session_id, 'activeSeconds': 60}),
            content_type='application/json',
        )

        # Agent session should be auto-ended
        act_session = ActivitySession.objects.get(id=act_session_id)
        self.assertFalse(act_session.is_active)
