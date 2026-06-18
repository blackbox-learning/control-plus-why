"""
ProcrastinaAI Tests — Report Generation & Idle Return
Tests report generation (manual + enhanced), idle-return options,
and saving return reasons.
"""

import json
from unittest.mock import patch
from django.test import TestCase, Client
from procrastina_ai.models import (
    Session, Disappearance, Report, ActivitySession,
    ActivityLog, ApplicationUsage,
)


class ReportGenerationTest(TestCase):
    """Tests for manual and enhanced report generation."""

    def setUp(self):
        self.client = Client()
        self.base = '/projects/procrastina-ai/api'
        # Create parent session
        resp = self.client.post(
            f'{self.base}/create-session/',
            data=json.dumps({
                'mood': 'lazy',
                'interests': ['YouTube', 'AI'],
                'tasks': ['Record video', 'Write blog', 'Fix bugs'],
            }),
            content_type='application/json',
        )
        self.session_id = resp.json()['data']['sessionId']
        self.session = Session.objects.get(id=self.session_id)

    # ------------------------------------------------------------------
    # Manual Report
    # ------------------------------------------------------------------

    @patch('procrastina_ai.services._call_ai')
    def test_manual_report(self, mock_ai):
        """Generate report without activity data should use manual report."""
        mock_ai.return_value = "You planned 3 things.\nYou did none.\nBut the YouTube algorithm thanks you."

        # Add some disappearances
        Disappearance.objects.create(
            session=self.session,
            disappearance_type='youtube',
            ai_response='You went for one video.',
        )

        resp = self.client.post(
            f'{self.base}/generate-report/',
            data=json.dumps({
                'sessionId': self.session_id,
                'tasksPlanned': 3,
                'tasksCompleted': 0,
                'disappearances': 1,
                'commonExcuse': 'youtube',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('procrastinationScore', data['data'])
        self.assertFalse(data['data']['hasActivityData'])

        # Verify Report record
        report = Report.objects.filter(session=self.session).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.tasks_planned, 3)

    # ------------------------------------------------------------------
    # Enhanced Report (with activity data)
    # ------------------------------------------------------------------

    @patch('procrastina_ai.services._call_ai')
    def test_enhanced_report(self, mock_ai):
        """Generate report with activity data should include topApps."""
        mock_ai.return_value = "You spent 45 min on YouTube.\nRespect the dedication."

        # Create activity session with data
        act_session = ActivitySession.objects.create(
            session=self.session,
            source='desktop_agent',
            is_active=False,
            total_active_seconds=3600,
            event_count=50,
        )
        ApplicationUsage.objects.create(
            activity_session=act_session,
            app_name='Google Chrome',
            category='entertainment',
            total_seconds=2700,
            focus_events=20,
        )
        ApplicationUsage.objects.create(
            activity_session=act_session,
            app_name='Visual Studio Code',
            category='development',
            total_seconds=900,
            focus_events=10,
        )

        resp = self.client.post(
            f'{self.base}/generate-report/',
            data=json.dumps({
                'sessionId': self.session_id,
                'tasksPlanned': 3,
                'tasksCompleted': 1,
                'disappearances': 0,
                'commonExcuse': 'Unknown',
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['hasActivityData'])

    # ------------------------------------------------------------------
    # Report Accuracy
    # ------------------------------------------------------------------

    @patch('procrastina_ai.services._call_ai')
    def test_report_accuracy(self, mock_ai):
        """Report score and disappearance count should match DB."""
        mock_ai.return_value = "Good summary."

        # Add 3 disappearances
        for dtype in ['youtube', 'ai_tools', 'startup']:
            Disappearance.objects.create(
                session=self.session,
                disappearance_type=dtype,
                ai_response=f'Response for {dtype}',
            )

        resp = self.client.post(
            f'{self.base}/generate-report/',
            data=json.dumps({
                'sessionId': self.session_id,
                'tasksPlanned': 3,
                'tasksCompleted': 1,
                'disappearances': 3,
                'commonExcuse': 'youtube',
            }),
            content_type='application/json',
        )
        data = resp.json()['data']
        self.assertEqual(data['totalDisappearances'], 3)
        self.assertIn('procrastinationScore', data)
        self.assertGreaterEqual(data['procrastinationScore'], 0)
        self.assertLessEqual(data['procrastinationScore'], 100)

    # ------------------------------------------------------------------
    # Insufficient Data Message
    # ------------------------------------------------------------------

    def test_insufficient_data_flag(self):
        """Session with < 30 seconds should have activity_data_sufficient=False."""
        # End session with minimal activity
        self.client.post(
            f'{self.base}/end-session/',
            data=json.dumps({'sessionId': self.session_id, 'activeSeconds': 5}),
            content_type='application/json',
        )
        session = Session.objects.get(id=self.session_id)
        self.assertFalse(session.activity_data_sufficient)

    # ------------------------------------------------------------------
    # Idle Return Options
    # ------------------------------------------------------------------

    @patch('procrastina_ai.services._call_ai')
    def test_idle_return_options(self, mock_ai):
        """GET idle-return-options should return a list of options."""
        mock_ai.return_value = (
            "youtube | YouTube Videos | Just one more, right?\n"
            "laptops | Laptop Research | Your current one is fine.\n"
            "ai_tools | AI Tool Hunting | Very productive.\n"
            "startup | Startup Ideas | Billion dollar timing.\n"
            "other | Something Else | Confess now."
        )

        resp = self.client.get(
            f'{self.base}/idle-return-options/',
            {'sessionId': self.session_id},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        options = data['data']['options']
        self.assertIsInstance(options, list)
        self.assertGreaterEqual(len(options), 3)

        # Each option should have type, label, sub
        for opt in options:
            self.assertIn('type', opt)
            self.assertIn('label', opt)
            self.assertIn('sub', opt)

    def test_idle_return_options_missing_session(self):
        """GET idle-return-options without sessionId should return 400."""
        resp = self.client.get(f'{self.base}/idle-return-options/')
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Save Return Reason
    # ------------------------------------------------------------------

    @patch('procrastina_ai.services._call_ai')
    def test_save_return_reason(self, mock_ai):
        """POST save-return-reason should create a Disappearance with AI response."""
        mock_ai.return_value = "You disappeared.\nThe AI noticed.\nWelcome back."

        resp = self.client.post(
            f'{self.base}/save-return-reason/',
            data=json.dumps({
                'sessionId': self.session_id,
                'reasonType': 'youtube',
                'customReason': '',
                'idleDurationSeconds': 600,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('aiResponse', data['data'])
        self.assertIn('disappearanceId', data['data'])

        # Verify Disappearance record
        dis = Disappearance.objects.get(id=data['data']['disappearanceId'])
        self.assertEqual(dis.disappearance_type, 'youtube')
        self.assertTrue(len(dis.ai_response) > 0)

    @patch('procrastina_ai.services._call_ai')
    def test_save_return_reason_other(self, mock_ai):
        """Saving 'other' reason should store custom_location."""
        mock_ai.return_value = "Mysterious disappearance noted."

        resp = self.client.post(
            f'{self.base}/save-return-reason/',
            data=json.dumps({
                'sessionId': self.session_id,
                'reasonType': 'other',
                'customReason': 'Watching the ceiling fan',
                'idleDurationSeconds': 300,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['success'])

        dis = Disappearance.objects.get(id=data['data']['disappearanceId'])
        self.assertEqual(dis.disappearance_type, 'other')
        self.assertEqual(dis.custom_location, 'Watching the ceiling fan')
