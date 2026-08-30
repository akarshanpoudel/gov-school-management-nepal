import openpyxl
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from .models import Exam, Subject, Mark

@login_required
def mark_entry_view(request, exam_id, subject_id):
    exam = get_object_or_404(Exam, id=exam_id)
    subject = get_object_or_404(Subject, id=subject_id)
    students = User.objects.filter(role=User.Role.STUDENT)

    if request.method == 'POST':
        for student in students:
            t_mark = request.POST.get(f"theory_{student.id}", 0)
            p_mark = request.POST.get(f"practical_{student.id}", 0)
            
            Mark.objects.update_or_create(
                student=student,
                exam=exam,
                subject=subject,
                defaults={
                    'theory_obtained': float(t_mark) if t_mark else 0.0,
                    'practical_obtained': float(p_mark) if p_mark else 0.0,
                }
            )
        return redirect('core:dashboard')

    existing_marks = {
        m.student_id: m for m in Mark.objects.filter(exam=exam, subject=subject)
    }

    context = {
        'exam': exam,
        'subject': subject,
        'students': students,
        'existing_marks': existing_marks,
    }
    return render(request, 'academics/mark_entry.html', context)

@login_required
def export_iemis_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "IEMIS Marks"

    headers = ["Student ID", "Student Name", "Subject Code", "Theory Marks", "Practical Marks", "Total Marks"]
    ws.append(headers)

    marks = Mark.objects.select_related('student', 'subject').all()
    for m in marks:
        ws.append([
            m.student.username,
            m.student.get_full_name() or m.student.username,
            m.subject.code,
            float(m.theory_obtained),
            float(m.practical_obtained),
            float(m.total_marks),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="IEMIS_Marks_Export.xlsx"'
    wb.save(response)
    return response

@login_required
def student_report_card_view(request, student_id, exam_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    exam = get_object_or_404(Exam, id=exam_id)
    marks = Mark.objects.filter(student=student, exam=exam).select_related('subject')

    total_credits = 0.0
    weighted_gp_sum = 0.0
    has_ng = False

    for mark in marks:
        credit = float(mark.subject.credit_hours)
        gp = mark.grade_point
        
        total_credits += credit
        weighted_gp_sum += (gp * credit)
        
        if mark.is_ng:
            has_ng = True

    final_gpa = 0.0 if (has_ng or total_credits == 0) else round(weighted_gp_sum / total_credits, 2)

    context = {
        'student': student,
        'exam': exam,
        'marks': marks,
        'final_gpa': final_gpa,
        'has_ng': has_ng,
        'total_credits': total_credits,
    }
    return render(request, 'academics/report_card.html', context)