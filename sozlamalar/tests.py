from django.test import TestCase
from rest_framework.test import APIClient


class CheckSettingsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_check_settings_get_and_put_work(self):
        get_response = self.client.get('/sozlamalar/check-settings/')
        self.assertEqual(get_response.status_code, 200)

        payload = {
            'cafe_name': 'Bahor Cafe',
            'phone': '+998901234567',
            'address': 'Toshkent sh., Mustaqillik ko\u2018chasi',
            'footer_text': 'Telegram kanalimizga obuna bo\u2018ling!',
            'show_cafe_name': True,
            'show_sana': True,
            'show_ish_vaqti': True,
            'show_sotuvchi': True,
            'show_kassir': True,
            'show_mijoz': True,
            'show_kontaktlar': True,
            'show_inn': True,
            'show_yuridik_shaxs': True,
            'show_manzil': False,
            'show_mijoz_raqami': True,
            'show_eslatma': True,
        }

        put_response = self.client.put('/sozlamalar/check-settings/', payload, format='json')
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.data['cafe_name'], 'Bahor Cafe')
