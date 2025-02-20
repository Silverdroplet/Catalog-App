from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView, CatalogView, CustomLoginView, dashboard_redirect,
    PatronDashboardView, LibrarianDashboardView
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("catalog/", CatalogView.as_view(), name="catalog"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("accounts/", include("allauth.urls")),  # Enables Google Login
    path("logout/", LogoutView.as_view(next_page="core:home"), name="logout"),
    path("dashboard/", dashboard_redirect, name="dashboard"),
    path("dashboard/patron/", PatronDashboardView.as_view(), name="patron"),
    path("dashboard/librarian/", LibrarianDashboardView.as_view(), name="librarian"),
]