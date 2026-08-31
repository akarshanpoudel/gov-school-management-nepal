from django.contrib import admin
from .models import FeeCategory, FeeStructure, Invoice, Payment

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'category', 'academic_year', 'amount')
    list_filter = ('academic_year', 'classroom')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'title', 'total_amount', 'paid_amount', 'remaining_balance', 'status', 'due_date')
    list_filter = ('status', 'academic_year')
    search_fields = ('student__username', 'student__first_name', 'student__last_name')
    inlines = [PaymentInline]