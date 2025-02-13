from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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
    if request.user.is_staff:
        return redirect("core:librarian")
    return redirect("core:patron")

class PatronDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "patron.html"

class LibrarianDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "librarian.html"
