from django.urls import path, include
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView, CatalogView, CustomLoginView, create_librarian_request, dashboard_redirect,
    PatronDashboardView, LibrarianDashboardView, upload_profile_picture,
    add_equipment, add_item_image, edit_equipment, delete_equipment, submit_review, add_collection,
    my_collections, edit_collection, view_collection, approve_access, collection_catalog, delete_collection,
    equipment_details_sidebar, search_users, add_item_to_collection, return_item, deny_access_request, request_borrow_item,
    approve_borrow_request, deny_borrow_request, approve_librarian_request,deny_librarian_request, past_librarian_requests,
    my_equipment, past_borrow_requests, about_collections, delete_item_image, request_item_back, suspend_user, 
    loan, suspended_users, unsuspend_user
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
    path('dashboard/librarian-request/', create_librarian_request, name='request-librarian'),
    path("dashboard/librarian-request/<int:request_id>/approve", approve_librarian_request, name='approve_librarian_request'),    
    path("dashboard/librarian-request/<int:request_id>/deny", deny_librarian_request, name='deny_librarian_request'),    
    path("dashboard/librarian/", LibrarianDashboardView.as_view(), name="librarian"),
    path('dashboard/librarian-request/past-requests', past_librarian_requests, name='past-librarian-requests'),
    path('dashboard/librarian/past-borrow-requests', past_borrow_requests, name='past_borrow_requests'),
    path("dashboard/upload-profile-picture/", upload_profile_picture, name="upload_profile_picture"),
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
    path('collections/<int:collection_id>/deny_access/<int:user_id>/', deny_access_request, name='deny_access_request'),
    path('catalog/collections', collection_catalog, name='collection_catalog'),
    path('collections/delete/<int:collection_id>/', delete_collection, name='delete_collection'),
    path('equipment/details/<int:item_id>/', equipment_details_sidebar, name='equipment_details_sidebar'),
    path('librarians/api/search-users/', search_users, name='search_users'),
    path('catalog/<int:item_id>/add-to-collection/', add_item_to_collection, name='add_item_to_collection'),
    path('equipment/<int:equipment_id>/return/', return_item, name='return_item'),
    path('equipment/<int:equipment_id>/request/', request_borrow_item, name='request_borrow_item'),
    path('borrow-request/<int:request_id>/approve/', approve_borrow_request, name='approve_borrow_request'),
    path('borrow-request/<int:request_id>/deny/', deny_borrow_request, name='deny_borrow_request'),
    path('dashboard/my_equipment', my_equipment, name='my_equipment'),
    path('about/collections', about_collections, name='about_collecitons'),
    path("dashboard/librarian/delete-item-image/<int:image_id>/", delete_item_image, name="delete_item_image"),
    path('request-item/<int:loan_id>', request_item_back, name="request_item_back"),
    path('suspend-user/<int:user_id>', suspend_user, name="suspend_user"),
    path('unsuspend-user/<int:user_id>', unsuspend_user, name="unsuspend_user"),
    path('loans', loan, name="loan"),
    path('suspended_users', suspended_users, name="suspended_users")

]