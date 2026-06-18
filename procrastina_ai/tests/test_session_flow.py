"""
ProcrastinaAI Tests — Session Flow
Tests the core session lifecycle: create → active → end → recovery.
"""

import json
from django.test import TestCase, Client
from procrastina_ai.models import Session, Disappearance


class SessionFlowTest(TestCase):
    """Tests for the main Session lifecycle endpoints."""

    def setUp(self):
        self.client = Client()
        self.base = '/projects/procrastina-ai/api'
        self.session_payload = {
            'mood': 'lazy',
            'interests': ['YouTube', 'AI', 'Gaming'],
            'tasks': ['Record video', 'Edit thumbnails', 'Write description'],
        }

    # ------------------------------------------------------------------
    # Create Session
    # ------------------------------------------------------------------

    def test_create_session(self):
        """POST create-session should create a DB record and return sessionId."""
        resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('sessionId', data['data'])
        # Verify DB record exists
        session = Session.objects.get(id=data['data']['sessionId'])
        self.assertEqual(session.mood, 'lazy')
        self.assertTrue(session.is_active)

    def test_create_session_missing_fields(self):
        """POST create-session without required fields should return 400."""
        resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps({'mood': 'lazy'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    # ------------------------------------------------------------------
    # End Session
    # ------------------------------------------------------------------

    def test_end_session(self):
        """POST end-session should mark session inactive and set ended_at."""
        # Create session first
        create_resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        session_id = create_resp.json()['data']['sessionId']

        # End session
        resp = self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': session_id, 'activeSeconds': 120}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])

        session = Session.objects.get(id=session_id)
        self.assertFalse(session.is_active)
        self.assertIsNotNone(session.ended_at)
        self.assertEqual(session.active_seconds, 120)

    def test_end_session_not_found(self):
        """POST end-session with invalid UUID should return 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        resp = self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': fake_id}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

    # ------------------------------------------------------------------
    # Session Data Retrieval
    # ------------------------------------------------------------------

    def test_session_data_retrieval(self):
        """GET session-data should return full session with disappearances."""
        # Create session
        create_resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        session_id = create_resp.json()['data']['sessionId']
        session = Session.objects.get(id=session_id)

        # Add a disappearance
        Disappearance.objects.create(
            session=session,
            disappearance_type='youtube',
            ai_response='You went for one video.',
        )

        # Fetch session data
        resp = self.client.get(
            f'{self.base}/session-data/',
            {'sessionId': session_id},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(data['sessionId'], session_id)
        self.assertEqual(len(data['disappearances']), 1)
        self.assertEqual(data['disappearances'][0]['type'], 'youtube')
        self.assertTrue(data['isActive'])

    def test_session_data_missing_session_id(self):
        """GET session-data without sessionId should return 400."""
        resp = self.client.get(f'{self.base}/session-data/')
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Session Recovery
    # ------------------------------------------------------------------

    def test_session_recovery_active(self):
        """GET recover-session should return active session."""
        # Create an active session
        create_resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        session_id = create_resp.json()['data']['sessionId']

        # Recover
        resp = self.client.get(f'{self.base}/recover-session/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertTrue(data['hasActiveSession'])
        self.assertEqual(data['sessionId'], session_id)

    def test_session_recovery_none(self):
        """GET recover-session with no active sessions should return hasActiveSession=False."""
        resp = self.client.get(f'{self.base}/recover-session/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertFalse(data['hasActiveSession'])

    # ------------------------------------------------------------------
    # Activity Data Sufficient Flag
    # ------------------------------------------------------------------

    def test_activity_data_sufficient_flag(self):
        """Session with >= 30 active seconds should set activity_data_sufficient=True."""
        create_resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        session_id = create_resp.json()['data']['sessionId']

        # End with 60 seconds
        self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': session_id, 'activeSeconds': 60}),
            content_type='application/json',
        )
        session = Session.objects.get(id=session_id)
        self.assertTrue(session.activity_data_sufficient)

    def test_activity_data_insufficient_flag(self):
        """Session with < 30 active seconds should keep activity_data_sufficient=False."""
        create_resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps(self.session_payload),
            content_type='application/json',
        )
        session_id = create_resp.json()['data']['sessionId']

        # End with only 10 seconds
        self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': session_id, 'activeSeconds': 10}),
            content_type='application/json',
        )
        session = Session.objects.get(id=session_id)
        self.assertFalse(session.activity_data_sufficient)
