from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.academics.models import ClassRoom, Exam, Subject, Attendance, Mark
from apps.fees.models import Invoice
from apps.users.models import User

@login_required
def dashboard_view(request):
    # Automatically route student users to their personal portal
    if request.user.role == User.Role.STUDENT:
        return redirect('core:student_dashboard')

    classrooms = ClassRoom.objects.all().order_by('name')
    exams = Exam.objects.all().order_by('-date_held')
    subjects = Subject.objects.all().order_by('code')
    students = User.objects.filter(role=User.Role.STUDENT).order_by('username')

    context = {
        'classrooms': classrooms,
        'exams': exams,
        'subjects': subjects,
        'students': students,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def student_dashboard_view(request):
    if request.user.role != User.Role.STUDENT:
        return redirect('core:dashboard')

    student = request.user
    attendance_records = Attendance.objects.filter(student=student).order_by('-date')
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status=Attendance.Status.PRESENT).count()
    attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 100.0

    invoices = Invoice.objects.filter(student=student).order_by('-due_date')
    marks = Mark.objects.filter(student=student).select_related('exam', 'subject')
    latest_exam = Exam.objects.order_by('-date_held').first()

    context = {
        'student': student,
        'attendance_pct': attendance_pct,
        'total_days': total_days,
        'present_days': present_days,
        'invoices': invoices,
        'marks': marks,
        'latest_exam': latest_exam,
    }
    return render(request, 'core/student_dashboard.html', context)