from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("School Admin / Headmaster")
        TEACHER = "TEACHER", _("Teacher")
        STAFF = "STAFF", _("Accountant / Staff")
        STUDENT = "STUDENT", _("Student")

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.TEACHER,
        help_text=_("Access level in the school system")
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    citizenship_no = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text=_("National Identification / Citizenship Number")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"