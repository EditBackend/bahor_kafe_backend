from django.test import TestCase
from rest_framework.test import APIClient


class TableLayoutEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_table_layout_get_and_post_work(self):
        get_response = self.client.get('/table/table-layout/')
        self.assertEqual(get_response.status_code, 200)

        payload = {
            'positions': {
                '1': {'x': 100, 'y': 200},
                '2': {'x': 350, 'y': 180},
            },
            'shapes': {
                '1': 'rectangle',
                '2': 'circle',
            },
        }

        post_response = self.client.post('/table/table-layout/', payload, format='json')
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(post_response.data['positions']['1']['x'], 100)
