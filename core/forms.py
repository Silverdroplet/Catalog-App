from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile, Equipment, EquipmentImage

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