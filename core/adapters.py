from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.groups.filter(name="Librarians").exists():
            return reverse("core:librarian")
        return reverse("core:patron")
