from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import Group, User
from django.shortcuts import reverse
from .models import Profile

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.groups.filter(name="Librarians").exists():
            return reverse("core:librarian")
        return reverse("core:patron")

    def pre_social_login(self, request, sociallogin):
        """This function runs before social login completes."""
        # If the user is already logged in, return
        if sociallogin.user.id:
            return
        
        email = sociallogin.account.extra_data.get("email")

        if email:
            try:
                # Check if a user already exists with the same email
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)  # Link Google login to existing user
            except User.DoesNotExist:
                pass  # Continue with new user creation

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if sociallogin and sociallogin.account.provider == "google":
            data = sociallogin.account.extra_data
            user.first_name = data.get("given_name", "")
            user.last_name = data.get("family_name", "")
            user.email = data.get("email", "")

            # Ensure profile exists
            profile, created = Profile.objects.get_or_create(user=user)
            profile.profile_picture = data.get("picture", "")
            profile.save()

        # Assign users to the "Patrons" group by default
        if not user.groups.exists():  # Check if user is in any group
            group, created = Group.objects.get_or_create(name="Patrons")
            user.groups.add(group)

        user.save()
        return user
