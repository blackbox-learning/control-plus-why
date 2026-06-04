from django.test import TestCase


class ProcrastinaAiViewsTest(TestCase):
    def test_index_status(self):
        resp = self.client.get('/projects/procrastina-ai/')
        self.assertEqual(resp.status_code, 200)
