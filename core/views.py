from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Equipment, Profile
from .forms import ProfileForm, EquipmentForm, ItemImageForm

class HomeView(TemplateView):
    template_name = "home.html"

class CatalogView(ListView):
    model = Equipment
    template_name = "catalog.html"
    context_object_name = "items"

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

class PatronDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "patron.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, created = Profile.objects.get_or_create(user=user)
        context["profile"] = profile
        context["name"] = user.first_name if user.first_name else "Guest"
        context["username"] = user.email.split('@')[0] if user.email else user.username
        context["email"] = user.email if user.email else "No email provided"
        return context

class LibrarianDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "librarian.html"

@login_required
def upload_profile_picture(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
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