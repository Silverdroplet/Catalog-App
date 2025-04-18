from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import Q

class Collection(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private')
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_collections')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    allowed_users = models.ManyToManyField(User, blank=True, related_name='allowed_collections')
    items = models.ManyToManyField('Equipment', related_name='collections', blank=True)
    access_requests = models.ManyToManyField(User, related_name='requested_collections', blank=True)
    modification_logs = models.TextField(blank=True, null=True) 
    def __str__(self):
        return self.title

    def is_accessible_by(self, user):
        return self.visibility == 'public' or user in self.allowed_users.all() or user.profile.is_librarian

    def clean(self):
        if self.pk:
            if self.visibility == 'private':
                for item in self.items.all():
                    private_collections = Collection.objects.filter(
                        visibility='private',
                        items=item
                    ).exclude(id=self.id)

                    if private_collections.exists():
                        raise ValidationError(
                            f'Item "{item}" is already in another private collection.'
                        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

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
    sports_type = models.CharField(max_length=100, blank=True)
    added_date = models.DateTimeField(auto_now_add=True)
    sports_type = models.CharField(max_length=100, null=True, blank=True)
    #current_user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, blank = True, related_name="borrowed_equipment")
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

class CollectionAccessRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} requested access to {self.collection.title}"
    
class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    item = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    patron = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')

    def __str__(self):
        return f"{self.patron.username} requested {self.item.name} ({self.status})"

class LibrarianRequests(models.Model):
    STATUS_CHOICES= [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    patron = models.ForeignKey(User, on_delete=models.CASCADE, related_name='librarian_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_librarian')

    def __str__(self):
        return f"{self.patron.username} requested to be a librarian"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:40]}"