from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from .models import Equipment, Profile, Review, Collection, User, Loan, LibrarianRequests, EquipmentImage
from .forms import ProfileForm, EquipmentForm, ItemImageForm, ReviewForm, CollectionForm
from django.http import HttpResponseRedirect
from .models import Collection, CollectionAccessRequest, BorrowRequest, Notification
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
        context["notifications"] = Notification.objects.filter(user=user).order_by("-created_at")[:10]
        context["user_request"] = LibrarianRequests.objects.filter(patron=user).order_by('-timestamp').first()
        return context
    
    def test_func(self):
        return self.request.user.groups.filter(name="Patrons").exists()
    def handle_no_permission(self):
        if self.request.user.groups.filter(name="Librarians").exists():
            return redirect('core:librarian')
        return redirect('core:home')

class LibrarianDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "librarian.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        context["profile"] = profile
        context["name"] = user.first_name if user.first_name else "Guest"
        context["username"] = user.email.split('@')[0] if user.email else user.username
        context["email"] = user.email if user.email else "No email provided"
        context["equipment_list"] = Loan.objects.filter(user=user, equipment__is_available=False)
        context["collections"] = Collection.objects.filter(creator=user)
        context["librarian_requests"] = LibrarianRequests.objects.filter(status="pending")
        context["borrow_requests"] = BorrowRequest.objects.filter(status="pending")
        context["notifications"] = Notification.objects.filter(user=user).order_by("-created_at")[:10]
        return context
    def test_func(self):
        return self.request.user.groups.filter(name="Librarians").exists()
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('core:patron')
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
        else: 
            messages.warning(request, "Your request was denied previously.")

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
        else: 
            messages.warning(request, "Your request was denied previously.")
        return HttpResponseRedirect(reverse('core:collection_catalog'))  
    access_requests = None
    if request.user.is_authenticated:
        for collection in collections:
            requite = CollectionAccessRequest.objects.filter(user=request.user, collection=collection).first()
            collection.user_access_request = requite
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
    if request.user.is_authenticated:
        collections = Collection.objects.filter(creator=request.user)
        if request.user.profile.is_librarian:
            collections = Collection.objects.all()
    else:
        collections = None
    loan = None
    user_request = None
    if request.user.is_authenticated:
        loan = Loan.objects.filter(equipment=item, user=request.user).order_by('-borrowedAt').first()
        user_request = item.borrow_requests.filter(patron=request.user).last()
    reviews = Review.objects.filter(equipment=item)
    html = render_to_string("equipment_sidebar.html", {
        "item": item,
        "collections": collections,
        "loan": loan,
        "reviews": reviews,
        "user_request": user_request,
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
def add_item_to_collection(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Equipment, id=item_id)
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id)

        if collection.visibility == 'private' and request.user not in collection.allowed_users.all() and not request.user.profile.is_librarian:
            messages.error(request, 'You do not have permission to add to this collection.')
            return redirect('core:catalog')

        collection.items.add(item)
        messages.success(request, f'Item added to the collection "{collection.title}".')
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
            equipment.current_user = None
            equipment.status = "checked-in"
            equipment.save()
            messages.success(request, f'You have successfully returned "{equipment.name}".')
            loan.delete()
        else:
            messages.error(request, "No loan record found for this item.")

    return redirect(request.META.get('HTTP_REFERER') or 'core:catalog')

@login_required
def deny_access_request(request, collection_id, user_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if collection.creator == request.user or request.user.profile.is_librarian:
        access_request = get_object_or_404(CollectionAccessRequest, collection=collection, user_id=user_id)
        access_request.status = 'Denied'
        access_request.save()
        collection.access_requests.remove(access_request.user)
        collection.save()

        return redirect('core:view_collection', collection_id=collection.id)

    return redirect('core:dashboard') 

@login_required
def request_borrow_item(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)

    #Prevent multiple requests
    existing = BorrowRequest.objects.filter(item=equipment, patron=request.user, status='pending').exists()
    if not equipment.is_available:
        messages.error(request, "This item is not available.")
    elif existing:
        messages.warning(request, "You already have a pending request for this item.")
    else:
        BorrowRequest.objects.create(item=equipment, patron=request.user)
        #Notify all librarians
        librarians = User.objects.filter(profile__is_librarian=True)
        for librarian in librarians:
            Notification.objects.create(
                user=librarian,
                message=f"📥 {request.user.username} requested to borrow '{equipment.name}'."
            )
        messages.success(request, "Borrow request submitted. A librarian will review it soon.")

    return redirect("core:catalog")

@login_required
def approve_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can approve requests.")

    #Approve the request
    borrow_request.status = "approved"
    borrow_request.reviewed_by = request.user
    borrow_request.decision_time = timezone.now()
    borrow_request.save()
    #Update the item
    equipment = borrow_request.item
    equipment.is_available = False
    equipment.status = "in-circulation"
    equipment.current_user = borrow_request.patron
    equipment.save()

    Notification.objects.create(
        user=borrow_request.patron,
        message=f"Your request to borrow '{borrow_request.item.name}' was approved!"
    )
    #Create the loan
    Loan.objects.create(
        user=borrow_request.patron,
        equipment=equipment,
        borrowedAt=timezone.now(),
        returnDate=timezone.now() + timedelta(days=7)
    )
    messages.success(request, f"Approved {borrow_request.patron.username}'s request for {equipment.name}.")
    return redirect("core:librarian")

@login_required
def deny_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)

    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can deny requests.")

    borrow_request.status = "denied"
    borrow_request.reviewed_by = request.user
    borrow_request.decision_time = timezone.now()
    borrow_request.save()

    Notification.objects.create(
        user=borrow_request.patron,
        message=f"Your request to borrow '{borrow_request.item.name}' was denied."
    )
    messages.info(request, f"Denied {borrow_request.patron.username}'s request for {borrow_request.item.name}.")
    return redirect("core:librarian")

@login_required
def create_librarian_request(request):
    if request.method == "POST":
        existing = LibrarianRequests.objects.filter(patron=request.user, status='pending').first()

        if existing:
            messages.warning(request, "You already have a pending librarian request")
        else:
            LibrarianRequests.objects.create(patron=request.user)
            #Notify all librarians
            librarian_group = Group.objects.get(name="Librarians")
            librarians = librarian_group.user_set.all()
            for librarian in librarians:
                Notification.objects.create(
                    user = librarian,
                    message=f"📥 {request.user.username} requested to be a librarian."
                )
            messages.success(request, "Request to be a librarian submitted. A librarian will review it soon.")

        return redirect("core:patron")

@login_required
def approve_librarian_request(request, request_id):
    librarian_request = get_object_or_404(LibrarianRequests, id=request_id)

    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can approve librarian requests.")
    
    #approve the request
    librarian_request.status = "approved"
    librarian_request.reviewed_by = request.user
    librarian_request.timestamp = timezone.now()
    librarian_request.save()

    #upgrade patron to librarian
    librarian_group, created = Group.objects.get_or_create(name="Librarians")
    patron_group, created = Group.objects.get_or_create(name="Patrons")
    librarian_request.patron.groups.add(librarian_group)
    librarian_request.patron.groups.remove(patron_group)
    librarian_request.patron.profile__is_librarian = True
    librarian_request.patron.save()

    #notify patron
    Notification.objects.create(
        user = librarian_request.patron,
        message=f"Your request to be a librarian was approved!"
    )

    messages.success(request, f"Approved {librarian_request.patron.username}'s request to be a librarian.")
    return redirect("core:librarian")

@login_required
def deny_librarian_request(request, request_id):
    librarian_request = get_object_or_404(LibrarianRequests, id=request_id)

    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can deny librarian requests.")
    
    librarian_request.status = "denied"
    librarian_request.reviewed_by = request.user
    librarian_request.timestamp = timezone.now()
    librarian_request.save()

    Notification.objects.create(
        user=librarian_request.patron,
        message=f"Your request to be a librarian was denied."
    )
    
    messages.info(request, f"Denied {librarian_request.patron.username}'s request to be a librarian.")
    return redirect("core:librarian")

@login_required
def past_librarian_requests(request):
    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can view past librarian requests.")
    
    past_denied_requests = LibrarianRequests.objects.filter(status="denied").order_by('-timestamp')
    past_approved_requests = LibrarianRequests.objects.filter(status="approved").order_by('-timestamp')

    return render(request, 'past_librarian_requests.html', {
        'past_denied_requests': past_denied_requests,
        'past_approved_requests': past_approved_requests
    })

@login_required
def my_equipment(request):
    equipment = Equipment.objects.filter(current_user = request.user).prefetch_related('images')

    return render(request, 'my_equipment.html', {
        'equipment': equipment,
    })

@login_required
def past_borrow_requests(request):
    if not request.user.groups.filter(name="Librarians").exists():
        return HttpResponseForbidden("Only librarians can view past librarian requests.")
    
    past_denied_requests = BorrowRequest.objects.filter(status="denied").order_by('-timestamp')
    past_approved_requests = BorrowRequest.objects.filter(status="approved").order_by('-timestamp')

    return render(request, 'past_borrow_requests.html', {
        'past_denied_requests': past_denied_requests,
        'past_approved_requests': past_approved_requests
    })

def about_collections(request):
    return render(request, 'about_collections.html')

@login_required
def delete_item_image(request, image_id):
    img = get_object_or_404(EquipmentImage, pk=image_id)
    equipment_id = img.equipment.id
    img.delete()
    return redirect("core:edit_equipment", equipment_id=equipment_id)
