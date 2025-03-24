from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile, Equipment, EquipmentImage, Review, Collection

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
        fields = ['name', 'identifier', 'description', 'is_available', 'status', 'location']

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

    class Meta:
        model = Collection
        fields = ['title', 'description', 'visibility', 'items']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
        if not user.profile.is_librarian:
            self.fields.pop('visibility')

        private_collections = Collection.objects.filter(visibility='private')
        private_items = Equipment.objects.filter(collections__in=private_collections).distinct()

        self.fields['items'].queryset = Equipment.objects.exclude(id__in=private_items)