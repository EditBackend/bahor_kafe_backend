from django.utils import timezone
from django.contrib.auth.models import update_last_login
class UpdateLastLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            update_last_login(None, request.user)
        response = self.get_response(request)
        return response