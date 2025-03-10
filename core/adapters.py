from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import reverse
from .models import Profile  # Import the Profile model
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import Group

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.groups.filter(name="Librarians").exists():
            return reverse("core:librarian")
        return reverse("core:patron")

    def save_user(self, request, user, form, commit = True):
        """save user details from Google OAuth and create a profile if needed!"""
        user = super().save_user(request, form, commit = False)

        #handle Google OAuth data
        sociallogin = getattr(user, 'sociallogin', None)
        
        if sociallogin and sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
            user.email = data.get('email', '')

            #ensure that the profile exists
            profile, created = Profile.objects.get_or_create(user = user)
            profile.profile_picture = data.get('picture', '') #google profile picture URL

            profile_picture_url = data.get('picture', '')  # Google profile picture URL
            print(f"Google Profile Picture URL: {profile_picture_url}")  # Log the URL
            profile.save()

        if commit:
            user.save()
        
        # Assign new users to "Patrons" group by default
        group, created = Group.objects.get_or_create(name="Patrons")
        user.groups.add(group)

        return user
