from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Equipment(models.Model):
    STATUS_CHOICES = [
        ('checked-in', 'Checked In'),
        ('in-circulation', 'In Circulation'),
        ('being-repaired', 'Being Repaired'),
    ]
    
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='checked-in')
    location = models.CharField(max_length=255, blank=True)
    added_date = models.DateTimeField(auto_now_add=True)
    # This field tracks which librarian added the item; enforce librarian-only access in your views.
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_equipments')
   
    def __str__(self):
        return self.name

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    borrowedAt = models.DateTimeField(default=timezone.now)
    returnDate = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} borrowed {self.equipment.name}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',  # folder prefix in S3
        blank=True,
        null=True
    )
    joined_date = models.DateTimeField(auto_now_add=True)
    is_librarian = models.BooleanField(default=False) 

    def __str__(self):
        return self.user.username
    
class EquipmentImage(models.Model):
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='equipment_images/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Image for {self.equipment.name}"