from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    classroom = models.ForeignKey(
        'academics.ClassRoom', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='students'
    )

    # Student Demographics & Guardian Details
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of Birth (AD)")
    father_name = models.CharField(max_length=150, blank=True, default="")
    mother_name = models.CharField(max_length=150, blank=True, default="")
    parent_phone = models.CharField(max_length=15, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="Pokhara, Kaski")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"