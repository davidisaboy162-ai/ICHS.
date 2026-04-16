from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    FARMER = "farmer"
    OFFICER = "extension_officer"
    ROLE_CHOICES = [
        (FARMER, "Farmer"),
        (OFFICER, "Extension Officer"),
    ]

    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=FARMER)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return self.username
