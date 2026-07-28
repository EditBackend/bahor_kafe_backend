from django.test import TestCase
from rest_framework.test import APIClient


class SupplierEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_suppliers_list_and_create_work(self):
        get_response = self.client.get('/inventory/suppliers/')
        self.assertEqual(get_response.status_code, 200)

        payload = {
            'name': 'Agro Food LLC',
            'phone': '+998901234567',
            'company_name': 'Agro Food',
        }

        post_response = self.client.post('/inventory/suppliers/', payload, format='json')
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(post_response.data['name'], 'Agro Food LLC')
