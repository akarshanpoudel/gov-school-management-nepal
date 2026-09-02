from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User
from apps.users.decorators import role_required
from apps.academics.models import ClassRoom, AcademicYear, Exam, Mark
from .models import FeeStructure, Invoice, Payment

# Every view below touches every student's financial or academic-standing
# data, or can mutate it (recording payments, promoting/graduating a whole
# class). The nav bar only links here for ADMIN users, but that's cosmetic —
# without @role_required, any authenticated account (including a student)
# could hit these URLs directly. Restricted to ADMIN accordingly.

@login_required
@role_required(User.Role.ADMIN)
def fee_dashboard_view(request):
    invoices = Invoice.objects.select_related('student').order_by('-created_at')
    total_due = sum(i.remaining_balance for i in invoices)
    total_collected = sum(i.paid_amount for i in invoices)

    context = {
        'invoices': invoices,
        'total_due': total_due,
        'total_collected': total_collected,
    }
    return render(request, 'fees/fee_dashboard.html', context)

@login_required
@role_required(User.Role.ADMIN)
def record_payment_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        remarks = request.POST.get('remarks', '')

        if amount > 0:
            Payment.objects.create(invoice=invoice, amount_paid=amount, remarks=remarks)
            messages.success(request, f"Payment of Rs. {amount} recorded successfully!")
            return redirect('fees:dashboard')

    context = {'invoice': invoice}
    return render(request, 'fees/record_payment.html', context)

@login_required
@role_required(User.Role.ADMIN)
def student_promotion_view(request):
    classrooms = ClassRoom.objects.all()
    academic_years = AcademicYear.objects.all()

    if request.method == 'POST':
        source_class_id = request.POST.get('source_class')
        target_class_id = request.POST.get('target_class')
        
        source_class = get_object_or_404(ClassRoom, id=source_class_id)
        target_class = get_object_or_404(ClassRoom, id=target_class_id) if target_class_id != 'GRADUATE' else None
        
        students = User.objects.filter(classroom=source_class, role=User.Role.STUDENT)
        promoted_count = 0

        for student in students:
            # Automatic Qualification Check: Must have no NG marks in latest exam
            latest_exam = Exam.objects.last()
            marks = Mark.objects.filter(student=student, exam=latest_exam)
            has_ng = any(m.is_ng for m in marks)

            if not has_ng:
                student.classroom = target_class
                student.save()
                promoted_count += 1

        messages.success(request, f"Successfully promoted {promoted_count} student(s) from {source_class} to {target_class or 'Graduated'}!")
        return redirect('core:dashboard')

    context = {
        'classrooms': classrooms,
        'academic_years': academic_years,
    }
    return render(request, 'fees/student_promotion.html', context)