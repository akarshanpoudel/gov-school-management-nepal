from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    classroom = models.ForeignKey('academics.ClassRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"