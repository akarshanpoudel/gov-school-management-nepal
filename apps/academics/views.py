from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.academics.models import ClassRoom, Exam, Subject, Mark, Attendance
from apps.users.models import User
from apps.users.decorators import role_required
import csv
import xml.etree.ElementTree as ET
from django.db.models import Count, Q

@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN)
def mark_entry_view(request, classroom_id, subject_id, exam_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    subject = get_object_or_404(Subject, id=subject_id)
    exam = get_object_or_404(Exam, id=exam_id)
    students = User.objects.filter(role=User.Role.STUDENT, classroom=classroom).order_by('username')

    if request.method == 'POST':
        for student in students:
            theory_val = request.POST.get(f'theory_{student.id}', '0')
            practical_val = request.POST.get(f'practical_{student.id}', '0')

            try:
                theory_marks = float(theory_val) if theory_val else 0.0
                practical_marks = float(practical_val) if practical_val else 0.0
            except ValueError:
                theory_marks, practical_marks = 0.0, 0.0

            mark_obj, _ = Mark.objects.get_or_create(
                student=student,
                subject=subject,
                exam=exam,
                defaults={'theory_marks': theory_marks, 'practical_marks': practical_marks}
            )
            mark_obj.theory_marks = theory_marks
            mark_obj.practical_marks = practical_marks
            mark_obj.save()

        messages.success(request, f'Marks saved successfully for {subject.name}!')
        return redirect('core:dashboard')

    existing_marks = {
        m.student_id: m for m in Mark.objects.filter(subject=subject, exam=exam, student__in=students)
    }

    context = {
        'classroom': classroom,
        'subject': subject,
        'exam': exam,
        'students': students,
        'existing_marks': existing_marks,
    }
    return render(request, 'academics/mark_entry.html', context)


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN)
def attendance_entry_view(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = User.objects.filter(role=User.Role.STUDENT, classroom=classroom).order_by('username')
    today = date.today()

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'PRESENT') 
            
            attendance_obj, _ = Attendance.objects.get_or_create(
                student=student,
                date=today,
                classroom=classroom,
                defaults={'status': status}
            )
            attendance_obj.status = status
            attendance_obj.save()

        messages.success(request, f"Attendance saved for {classroom.name} on {today.strftime('%b %d, %Y')}!")
        return redirect('core:dashboard')

    existing_attendance = {
        a.student_id: a for a in Attendance.objects.filter(student__in=students, date=today)
    }

    context = {
        'classroom': classroom,
        'students': students,
        'today': today,
        'existing_attendance': existing_attendance,
    }
    return render(request, 'academics/attendance_entry.html', context)


# REMAINING STUBS

@login_required
def report_card_view(request, student_id, exam_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    exam = get_object_or_404(Exam, id=exam_id)
    marks = Mark.objects.filter(student=student, exam=exam).select_related('subject')

    total_theory = sum(m.theory_marks for m in marks)
    total_practical = sum(m.practical_marks for m in marks)
    grand_total = total_theory + total_practical

    context = {
        'student': student,
        'exam': exam,
        'marks': marks,
        'total_theory': total_theory,
        'total_practical': total_practical,
        'grand_total': grand_total,
        'today': date.today(),
    }
    return render(request, 'academics/report_card.html', context)


@login_required
def character_certificate_view(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    
    context = {
        'student': student,
        'issue_date': date.today(),
    }
    return render(request, 'academics/character_certificate.html', context)


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN)
def attendance_report_view(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = User.objects.filter(role=User.Role.STUDENT, classroom=classroom).order_by('username')

    student_summary = []
    for student in students:
        total_days = Attendance.objects.filter(student=student, classroom=classroom).count()
        present_days = Attendance.objects.filter(student=student, classroom=classroom, status='PRESENT').count()
        absent_days = total_days - present_days
        percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0.0

        student_summary.append({
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'percentage': percentage,
        })

    context = {
        'classroom': classroom,
        'student_summary': student_summary,
    }
    return render(request, 'academics/attendance_report.html', context)


@login_required
@role_required(User.Role.ADMIN)
def export_iemis_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="iemis_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Username', 'Full Name', 'Classroom', 'Role'])

    students = User.objects.filter(role=User.Role.STUDENT).select_related('classroom')
    for s in students:
        writer.writerow([
            s.id,
            s.username,
            s.get_full_name() or s.username,
            s.classroom.name if getattr(s, 'classroom', None) else '',
            s.role
        ])

    return response


@login_required
@role_required(User.Role.ADMIN)
def export_iemis_xml_view(request):
    root = ET.Element('IEMISData')
    students_node = ET.SubElement(root, 'Students')

    students = User.objects.filter(role=User.Role.STUDENT).select_related('classroom')
    for s in students:
        student_el = ET.SubElement(students_node, 'Student')
        ET.SubElement(student_el, 'ID').text = str(s.id)
        ET.SubElement(student_el, 'Username').text = s.username
        ET.SubElement(student_el, 'FullName').text = s.get_full_name() or s.username
        ET.SubElement(student_el, 'Classroom').text = s.classroom.name if getattr(s, 'classroom', None) else ''

    xml_data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    response = HttpResponse(xml_data, content_type='application/xml')
    response['Content-Disposition'] = 'attachment; filename="iemis_export.xml"'
    return response