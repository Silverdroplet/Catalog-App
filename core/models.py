from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Equipment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    borrowedAt = models.DateTimeField(default=timezone.now)
    returnDate = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} borrowed {self.equipment.name}"