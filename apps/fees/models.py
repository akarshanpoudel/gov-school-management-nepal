from django.db import models
from django.conf import settings
from apps.academics.models import ClassRoom, AcademicYear

class FeeCategory(models.Model):
    name = models.CharField(max_length=100, help_text="e.g., Monthly Tuition, Admission, Examination")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='fee_structures')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('academic_year', 'classroom', 'category')

    def __str__(self):
        return f"{self.classroom} - {self.category.name}: Rs. {self.amount}"

class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PARTIAL = 'PARTIAL', 'Partially Paid'
        PAID = 'PAID', 'Paid'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    title = models.CharField(max_length=150, help_text="e.g., Baisakh 2081 Tuition Fee")
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount

    def update_status(self):
        if self.paid_amount >= self.total_amount:
            self.status = self.Status.PAID
        elif self.paid_amount > 0:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.UNPAID
        self.save()

    def __str__(self):
        return f"Invoice #{self.id} - {self.student.username} ({self.status})"

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto recalculate parent invoice balance
        total_paid = sum(p.amount_paid for p in self.invoice.payments.all())
        self.invoice.paid_amount = total_paid
        self.invoice.update_status()

    def __str__(self):
        return f"Payment Rs. {self.amount_paid} for Invoice #{self.invoice.id}"