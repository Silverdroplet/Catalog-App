from django.contrib import admin
from .models import Profile
from .models import Equipment, EquipmentImage 

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_librarian", "joined_date")

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'status', 'is_available', 'location', 'added_date', 'added_by')

@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'caption', 'image')
