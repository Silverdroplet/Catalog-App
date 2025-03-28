from django.contrib import admin
from .models import Profile, Equipment, EquipmentImage, Collection, CollectionAccessRequest

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_librarian", "joined_date")

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'status', 'is_available', 'location', 'added_date', 'added_by')

@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'caption', 'image')

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'visibility')
    search_fields = ('title', 'creator__username')
    list_filter = ('visibility',)

@admin.register(CollectionAccessRequest)
class CollectionAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'collection', 'status', 'timestamp')