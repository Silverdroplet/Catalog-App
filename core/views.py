from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView
from .models import Equipment
from django.urls import reverse_lazy

class HomeView(TemplateView):
    template_name = "home.html"

class CatalogView(ListView):
    model = Equipment
    template_name = "catalog.html"
    context_object_name = "items"

class CustomLoginView(LoginView):
    template_name = "login.html"

    from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_staff:
            return reverse_lazy("core:librarian")
        return reverse_lazy("core:patron")

@login_required
def dashboard_redirect(request):
    user = request.user

    if user.groups.filter(name="Librarians").exists():
        return redirect("core:librarian")
    else:
        return redirect("core:patron")

class PatronDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "patron.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["name"] = user.first_name if user.first_name else "Guest"
        context["username"] = user.username
        return context

class LibrarianDashboardView(TemplateView):
    template_name = "librarian.html"
