from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile, Equipment, EquipmentImage, Review, Collection, User
from django.contrib import messages
from django.db.models import Q

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

# Renamed to ProfileForm since our model is Profile
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'identifier', 'description', 'is_available', 'status', 'location', 'sports_type']

class ItemImageForm(forms.ModelForm):
    class Meta:
        model = EquipmentImage
        fields = ['image', 'caption']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

class CollectionForm(forms.ModelForm):
    items = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        widget=forms.CheckboxSelectMultiple,  
        required=False
    )

    allowed_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__is_librarian=False),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Collection
        fields = ['title', 'description', 'visibility', 'items', 'allowed_users']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        user = kwargs.pop('user', None)
        instance = kwargs.get('instance')  
        super().__init__(*args, **kwargs)

        self.fields['allowed_users'].queryset = User.objects.filter(profile__is_librarian=False)

        if not user.profile.is_librarian:
            self.fields.pop('visibility')

        private_collections = Collection.objects.filter(visibility='private')

        private_items = Equipment.objects.filter(collections__in=private_collections).distinct()

        if instance:
            self.fields['items'].queryset = Equipment.objects.filter(
                Q(id__in=instance.items.values_list('id', flat=True)) | ~Q(id__in=private_items)
            )
        else:
            self.fields['items'].queryset = Equipment.objects.exclude(id__in=private_items)

    
    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.visibility == 'private':
            for item in self.cleaned_data['items']:
                public_collections = item.collections.filter(visibility='public')
                if public_collections.exists():
                    for public_collection in public_collections:
                        public_collection.items.remove(item)
                        public_collection.save()

                        log_entry = f"Item '{item.name}' removed from Collection: '{public_collection.title}'. It was moved to a private collection by an administrator."
                        if public_collection.modification_logs:
                            public_collection.modification_logs += f"\n{log_entry}"
                        else:
                            public_collection.modification_logs = log_entry
                        public_collection.save()

        if commit:
            instance.save()
            self.save_m2m()
        
        return instance
