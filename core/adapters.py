from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import reverse
from .models import Profile  # Import the Profile model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.groups.filter(name="Librarians").exists():
            return reverse("core:librarian")
        return reverse("core:patron")
    def save_user(self, request, sociallogin, form=None):
        """save user details from Google OAuth and create a profile if needed!"""
        user = super().save_user(request, sociallogin, form)
        if sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
            user.email = data.get('email', '')
            user.save()

            #ensure that the profile exists
            profile, created = Profile.objects.get_or_create(user = user)
            profile.profile_picture = data.get('picture', '') #google profile picture URL
            profile.save()
        return user
