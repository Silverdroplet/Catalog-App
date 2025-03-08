from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import reverse
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import Group

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.groups.filter(name="Librarians").exists():
            return reverse("core:librarian")
        return reverse("core:patron")
class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if commit:
            user.save()
        # Assign new users to "Patrons" group by default
        group, created = Group.objects.get_or_create(name="Patrons")
        user.groups.add(group)
        return user
