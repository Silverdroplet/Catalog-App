from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView, CatalogView, CustomLoginView, dashboard_redirect,
    PatronDashboardView, LibrarianDashboardView, upload_profile_picture, 
    add_equipment, add_item_image, edit_equipment, delete_equipment, submit_review
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
    path("dashboard/patron/upload-profile-picture/", upload_profile_picture, name="upload_profile_picture"),
    path("dashboard/librarian/add-equipment/", add_equipment, name="add_equipment"),
    path("dashboard/librarian/edit-equipment/<int:equipment_id>/", edit_equipment, name="edit_equipment"),
    path("equipment/<int:equipment_id>/delete/", delete_equipment, name="delete_equipment"),
    path("dashboard/librarian/add-item-image/<int:item_id>/", add_item_image, name="add_item_image"),
    path("submit_review/<int:item_id>/", submit_review, name="submit_review"),
]