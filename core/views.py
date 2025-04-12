from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from .models import Equipment, Profile, Review, Collection, User, Loan
from .forms import ProfileForm, EquipmentForm, ItemImageForm, ReviewForm, CollectionForm
from django.http import HttpResponseRedirect
from .models import Collection, CollectionAccessRequest
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

class HomeView(TemplateView):
    template_name = "home.html"

class CatalogView(ListView):
    model = Equipment
    template_name = "catalog.html"
    context_object_name = "items"

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.profile.is_librarian:
            base_queryset = Equipment.objects.all()
        else:
            base_queryset = Equipment.objects.filter(
                Q(collections__visibility='public') | Q(collections__isnull=True)
            ).distinct()

        selected_gym = self.request.GET.get("location")
        if selected_gym:
            base_queryset = base_queryset.filter(location=selected_gym)
        
        selected_sport = self.request.GET.get("sport")
        if selected_sport:
            base_queryset = base_queryset.filter(sports_type=selected_sport)

        search_query = self.request.GET.get("q")
        if search_query:
            base_queryset = base_queryset.filter(name__icontains=search_query)

        return base_queryset

    def get_context_data(self, **kwargs):
        """Fetch all reviews and pass them to catalog.html"""
        context = super().get_context_data(**kwargs)
        context["gyms"] = Equipment.objects.values_list("location", flat=True).distinct()
        context["selected_gym"] = self.request.GET.get("location", "")
        context["sports"] = Equipment.objects.values_list("sports_type", flat=True).distinct()
        context["selected_sport"] = self.request.GET.get("sport", "")
        context["reviews"] = Review.objects.select_related("equipment", "user").all()
        context["review_form"] = ReviewForm() 
        return context

class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        user = self.request.user
        # If using groups for dashboard redirect, you might check here.
        if user.groups.filter(name="Librarians").exists():
            return reverse_lazy("core:librarian")
        return reverse_lazy("core:patron")

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.groups.filter(name="Librarians").exists():
        return redirect("core:librarian")
    else:
        return redirect("core:patron")

class PatronDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "patron.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        context["profile"] = profile
        context["name"] = user.first_name if user.first_name else "Guest"
        context["username"] = user.email.split('@')[0] if user.email else user.username
        context["email"] = user.email if user.email else "No email provided"
        context["equipment_list"] = Loan.objects.filter(user=user, equipment__is_available=False)
        return context
    
    def test_func(self):
        return self.request.user.groups.filter(name="Patrons").exists()
    def handle_no_permission(self):
        return redirect('core:home')

class LibrarianDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "librarian.html"

    def test_func(self):
        return self.request.user.groups.filter(name="Librarians").exists()
    def handle_no_permission(self):
        return redirect('core:home')
    
@login_required
def upload_profile_picture(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            if request.user.profile.is_librarian:
                return redirect('core:librarian')
            else:
                return redirect('core:patron')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'upload_profile_picture.html', {'form': form})


@login_required
def add_equipment(request):
    # Ensure the user is a librarian.
    if not request.user.profile.is_librarian:
        return HttpResponseForbidden("You do not have permission to add equipment.")

    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.added_by = request.user
            equipment.save()
            return redirect('core:catalog')
    else:
        form = EquipmentForm()
    return render(request, 'add_equipment.html', {'form': form})

@login_required
def edit_equipment(request, equipment_id):
    # Ensure the user is a librarian.
    if not request.user.profile.is_librarian:
        return HttpResponseForbidden("You do not have permission to edit equipment.")
    
    equipment = get_object_or_404(Equipment, id=equipment_id)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipment updated successfully.")
            return redirect('core:catalog')
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'edit_equipment.html', {'form': form, 'equipment': equipment})

@login_required
def delete_equipment(request, equipment_id):
    # Ensure the user is a librarian.
    if not request.user.profile.is_librarian:
        return HttpResponseForbidden("You do not have permission to delete equipment.")
    
    equipment = get_object_or_404(Equipment, id=equipment_id)
    
    if request.method == "POST":
        # Deleting equipment cascades to delete related EquipmentImage records.
        equipment.delete()
        messages.success(request, "Equipment and its images were deleted successfully.")
        return redirect('core:catalog')
    
    # Render a confirmation page.
    return render(request, 'confirm_delete.html', {'equipment': equipment})

@login_required
def add_item_image(request, item_id):
    # Ensure the user is a librarian.
    if not request.user.profile.is_librarian:
        return HttpResponseForbidden("You do not have permission to add images.")
    
    item = get_object_or_404(Equipment, id=item_id)
    
    if request.method == 'POST':
        form = ItemImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_instance = form.save(commit=False)
            image_instance.equipment = item
            image_instance.save()
            messages.success(request, "Image added successfully.")
            # Redirect back to the edit page so that images can be reviewed.
            return redirect('core:edit_equipment', equipment_id=item.id)
    else:
        form = ItemImageForm()
    
    return render(request, 'add_item_image.html', {'form': form, 'item': item})

@login_required
def submit_review(request, item_id):
    """Handles the submission of new reviews."""
    item = get_object_or_404(Equipment, id=item_id)
    
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.equipment = item
            review.user = request.user
            review.save()
            messages.success(request, "Your review has been submitted.")
            return redirect("core:catalog")

        # If form is invalid, re-render catalog page with errors
        messages.error(request, "There was an error submitting your review.")
        return render(
            request,
            "catalog.html",
            {"items": Equipment.objects.all(), "reviews": Review.objects.all(), "review_form": form}
        )
    return redirect("core:catalog")

@login_required
def add_collection(request):
    if request.method == 'POST':
        form = CollectionForm(request.POST, user=request.user, request=request)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.creator = request.user  
            if not request.user.profile.is_librarian:
                collection.visibility = 'public'  
            collection.save()
            form.save_m2m() 
            librarian_users = User.objects.filter(profile__is_librarian=True)
            collection.allowed_users.add(*librarian_users)
            return redirect('core:view_collection', collection_id=collection.id)
    else:
        form = CollectionForm(user=request.user)
    return render(request, 'add_collections.html', {'form': form})

@login_required
def my_collections(request):
    collections = Collection.objects.filter(creator=request.user)

    collection_requests = {
        collection.id: collection.access_requests.all()
        for collection in collections
    }
    modification_logs = {}  
    for collection in collections:
        images = []
        for item in collection.items.all():
            images.extend(item.images.all())  
        collection.image_list = images
    for collect in collections:
        logs = collect.modification_logs.splitlines() if collect.modification_logs else []
        if logs:
            modification_logs[collect.id] = logs
        with transaction.atomic():  
            collect.modification_logs = ""  
            collect.save()
    if request.method == "POST":
        collection_id = request.POST.get("collection_id")
        user_id = request.POST.get("user_id")
        
        if collection_id and user_id:
            collection = get_object_or_404(Collection, id=collection_id)
            user = get_object_or_404(User, id=user_id)

            if request.user.profile.is_librarian:
                collection.allowed_users.add(user)  
                collection.access_requests.remove(user) 
                collection.save()
                messages.success(request, f"Access granted to {user.username} for {collection.title}.")

    return render(request, 'view_collections.html', {
        'collections': collections,
        'collection_requests': collection_requests, 
        'modification_logs': modification_logs
    })

@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(
        Collection.objects.filter(
            Q(id=collection_id) & (Q(creator=request.user) | Q(allowed_users=request.user))
        ).distinct()
    )

    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection, user=request.user)
        if form.is_valid():
            form.save()
            librarian_users = User.objects.filter(profile__is_librarian=True)
            collection.allowed_users.add(*librarian_users)
            return redirect('core:my_collections')
    else:
        form = CollectionForm(instance=collection, user=request.user)
    return render(request, 'edit_collection.html', {'form': form, 'collection': collection})

def view_collection(request, collection_id):
    query = request.GET.get('q', '')  
    collection = get_object_or_404(Collection, id=collection_id)
    items = collection.items.all()  
    if query:
        items = items.filter(Q(name__icontains=query))

    if collection.visibility == 'public' or request.user.profile.is_librarian:
        return render(request, 'collection.html', {'collection': collection, 'query': query, 'items': items})

    if request.user in collection.access_requests.all():
        return render(request, 'collection.html', {'collection': collection, 'query': query, 'items': items})

    if request.method == "POST" and "request_access" in request.POST:
        existing_request = CollectionAccessRequest.objects.filter(user=request.user, collection=collection).first()
        if not existing_request:
            CollectionAccessRequest.objects.create(user=request.user, collection=collection)
            collection.access_requests.add(request.user) 
            collection.save()
            messages.success(request, "Your request has been submitted.")

        return HttpResponseRedirect(reverse('core:view_collection', args=[collection.id]))  

    access_request = CollectionAccessRequest.objects.filter(user=request.user, collection=collection).first()
    
    return render(request, 'collection.html', {'collection': collection, 'access_request': access_request, 'query': query, 'items': items})

@login_required
def approve_access(request, collection_id, user_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if collection.creator == request.user or request.user.profile.is_librarian:
        access_request = get_object_or_404(CollectionAccessRequest, collection=collection, user_id=user_id)
        access_request.approved = True
        access_request.save()
        collection.allowed_users.add(access_request.user)
        collection.access_requests.remove(access_request.user)
        collection.save()
        access_request.delete()

        return redirect('core:view_collection', collection_id=collection.id)

    return redirect('core:dashboard') 

def collection_catalog(request):
    query = request.GET.get('q', '')  
    collections = Collection.objects.filter(visibility='public')

    if request.user.is_authenticated:
        collections = Collection.objects.all()

    if query:
        collections = collections.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(items__name__icontains=query))

    for collection in collections:
        images = []
        for item in collection.items.all():
            images.extend(item.images.all())  
        collection.image_list = images

    if request.user.is_authenticated and request.method == "POST" and "request_access" in request.POST:
        collection_id = request.POST.get("collection_id")
        collection = get_object_or_404(Collection, id=collection_id)
        existing_request = CollectionAccessRequest.objects.filter(user=request.user, collection=collection).first()
        if not existing_request:
            CollectionAccessRequest.objects.create(user=request.user, collection=collection)
            collection.access_requests.add(request.user) 
            collection.save()
            messages.success(request, "Your request has been submitted.")

        return HttpResponseRedirect(reverse('core:collection_catalog'))  
    access_requests = None
    if request.user.is_authenticated:
        access_requests = {
            collection.id: CollectionAccessRequest.objects.filter(user=request.user, collection=collection).exists()
            for collection in collections
        }

    return render(request, 'collection_catalog.html', {
        'collections': collections,
        'query': query,
        'access_requests': access_requests 
    })

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if request.user == collection.creator or request.user.profile.is_librarian:
        collection.delete()
        messages.success(request, f'Collection "{collection.title}" deleted successfully.')
    else:
        messages.error(request, "You do not have permission to delete this collection.")

    return redirect('core:my_collections')  

def equipment_details_sidebar(request, item_id):
    item = get_object_or_404(Equipment, id=item_id)
    loan = Loan.objects.filter(equipment=item, user=request.user).order_by('-borrowedAt').first()
    reviews = Review.objects.filter(equipment=item)
    html = render_to_string("equipment_sidebar.html", {
        "item": item,
        "loan": loan,
        "reviews": reviews
    }, request=request)
    return HttpResponse(html)

@login_required
def search_users(request):
    if not request.user.profile.is_librarian or not request.user.is_authenticated:
        return HttpResponseForbidden("You do not have permission to access this.")
    query = request.GET.get("q", "")
    if len(query) < 3:
        return JsonResponse([], safe=False)
    results = User.objects.filter(username__icontains=query)[:20]
    return JsonResponse([
        {"id": u.id, "username": u.username, "email": u.email}
        for u in results
    ], safe=False)

@login_required
def borrow_item(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    if equipment.is_available:
        equipment.is_available = False
        equipment.save()
        #We create a loan record (default return a week later for now)
        Loan.objects.create(
            user=request.user,
            equipment=equipment,
            borrowedAt=timezone.now(),
            returnDate=timezone.now() + timedelta(days=7)
        )
    return redirect('core:catalog')

@login_required
def return_item(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    loan = Loan.objects.filter(equipment=equipment, user=request.user).order_by('-borrowedAt').first()
    if equipment.is_available:
        messages.error(request, "This item is still available.")
        return redirect('core:catalog')
    else:
        if loan:
            equipment.is_available = True
            equipment.save()
            messages.success(request, f'You have successfully returned "{equipment.name}".')
            loan.delete()
        else:
            messages.error(request, "No loan record found for this item.")

    return redirect('core:catalog')
    