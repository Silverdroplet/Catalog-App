from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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

class Review(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.equipment.name} ({self.rating})"
    
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

# Auto-create a Profile when a new User is created
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
    
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
    def delete(self, *args, **kwargs):
        """Override delete to remove the file from S3 (or configured storage) before deleting the record."""
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)