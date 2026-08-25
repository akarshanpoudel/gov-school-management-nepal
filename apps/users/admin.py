from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Columns displayed in the user list table
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    
    # Sidebar filters
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    # Search functionality
    search_fields = ('username', 'first_name', 'last_name', 'email', 'citizenship_no', 'phone_number')
    
    # Group custom government fields in the user edit view
    fieldsets = UserAdmin.fieldsets + (
        ('Government SMS Attributes', {
            'fields': ('role', 'phone_number', 'citizenship_no')
        }),
    )
    
    # Group custom government fields in the user creation view
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Government SMS Attributes', {
            'fields': ('role', 'phone_number', 'citizenship_no')
        }),
    )