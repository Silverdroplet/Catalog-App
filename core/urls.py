from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView, CatalogView, CustomLoginView, dashboard_redirect,
    PatronDashboardView, LibrarianDashboardView, upload_profile_picture, 
    add_equipment, add_item_image, edit_equipment, delete_equipment, submit_review, add_collection, 
    my_collections, edit_collection, view_collection, approve_access, collection_catalog, delete_collection, 
    equipment_details_sidebar, search_users, borrow_item, add_item_to_collection
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
    path('dashboard/collections/add/', add_collection, name='add_collection'),
    path('dashboard/collections', my_collections, name='my_collections'),
    path('collections/<int:collection_id>/', view_collection, name='view_collection'),
    path('dashboard/collections/edit/<int:collection_id>/', edit_collection, name='edit_collection'),
    path('collections/<int:collection_id>/approve_access/<int:user_id>/', approve_access, name='approve_access'),
    path('catalog/collections', collection_catalog, name='collection_catalog'),
    path('collections/delete/<int:collection_id>/', delete_collection, name='delete_collection'),
    path('equipment/details/<int:item_id>/', equipment_details_sidebar, name='equipment_details_sidebar'),
    path('librarians/api/search-users/', search_users, name='search_users'),
    path('equipment/<int:equipment_id>/borrow/', borrow_item, name='borrow_item'),
    path('catalog/<int:item_id>/add-to-collection/', add_item_to_collection, name='add_item_to_collection'),
]