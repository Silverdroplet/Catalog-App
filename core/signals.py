from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, EquipmentImage

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is created."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile whenever the User is saved."""
    instance.profile.save()

@receiver(pre_delete, sender=EquipmentImage)
def delete_equipment_image_file(sender, instance, **kwargs):
    """
    Deletes the file associated with an EquipmentImage instance from S3
    before the record is deleted.
    """
    if instance.image:
        instance.image.delete(save=False)

@receiver(pre_delete, sender=Profile)
def delete_profile_picture_file(sender, instance, **kwargs):
    """
    Deletes the profile picture file from S3 when a Profile is deleted.
    """
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)
