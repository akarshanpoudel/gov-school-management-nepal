import openpyxl
import xml.etree.ElementTree as ET
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from apps.users.decorators import role_required
from .models import Exam, Subject, Mark, ClassRoom, Attendance

@login_required
@role_required(User.Role.ADMIN, User.Role.TEACHER)
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
@role_required(User.Role.ADMIN, User.Role.TEACHER)
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
@role_required(User.Role.ADMIN, User.Role.TEACHER)
def export_iemis_xml(request):
    root = ET.Element("IEMIS_Student_Data", year="2081", country="Nepal")
    students_node = ET.SubElement(root, "Students")

    students = User.objects.filter(role=User.Role.STUDENT).select_related('classroom')
    for student in students:
        student_el = ET.SubElement(students_node, "Student")
        ET.SubElement(student_el, "EMIS_ID").text = str(student.username)
        ET.SubElement(student_el, "FullName").text = str(student.get_full_name() or student.username)
        ET.SubElement(student_el, "Grade").text = str(student.classroom.name if student.classroom else "N/A")
        
        marks_node = ET.SubElement(student_el, "AcademicPerformance")
        marks = Mark.objects.filter(student=student).select_related('subject')
        for m in marks:
            mark_el = ET.SubElement(marks_node, "SubjectMark")
            ET.SubElement(mark_el, "SubjectCode").text = str(m.subject.code)
            ET.SubElement(mark_el, "TheoryObtained").text = str(m.theory_obtained)
            ET.SubElement(mark_el, "PracticalObtained").text = str(m.practical_obtained)
            ET.SubElement(mark_el, "GradePoint").text = str(m.grade_point)
            ET.SubElement(mark_el, "IsNG").text = str(m.is_ng)

    tree = ET.ElementTree(root)
    response = HttpResponse(content_type='application/xml')
    response['Content-Disposition'] = 'attachment; filename="IEMIS_National_Data.xml"'
    tree.write(response, encoding='utf-8', xml_declaration=True)
    return response

@login_required
def student_report_card_view(request, student_id, exam_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    
    # RBAC: Students can only view their own report card
    if request.user.role == User.Role.STUDENT and request.user.id != student.id:
        return render(request, '403.html', status=403)

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

@login_required
@role_required(User.Role.ADMIN, User.Role.TEACHER)
def attendance_entry_view(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = User.objects.filter(classroom=classroom, role=User.Role.STUDENT)
    selected_date_str = request.GET.get('date', str(date.today()))

    if request.method == 'POST':
        entry_date = request.POST.get('attendance_date', str(date.today()))
        for student in students:
            status = request.POST.get(f"status_{student.id}", Attendance.Status.PRESENT)
            remarks = request.POST.get(f"remarks_{student.id}", "")
            Attendance.objects.update_or_create(
                student=student,
                date=entry_date,
                defaults={
                    'classroom': classroom,
                    'status': status,
                    'remarks': remarks
                }
            )
        return redirect('academics:attendance_report', classroom_id=classroom.id)

    existing_attendance = {
        a.student_id: a for a in Attendance.objects.filter(classroom=classroom, date=selected_date_str)
    }

    context = {
        'classroom': classroom,
        'students': students,
        'selected_date': selected_date_str,
        'existing_attendance': existing_attendance,
        'statuses': Attendance.Status.choices,
    }
    return render(request, 'academics/attendance_entry.html', context)

@login_required
def attendance_report_view(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = User.objects.filter(classroom=classroom, role=User.Role.STUDENT)

    report_data = []
    for student in students:
        total_days = Attendance.objects.filter(student=student, classroom=classroom).count()
        present_days = Attendance.objects.filter(student=student, classroom=classroom, status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]).count()
        absent_days = Attendance.objects.filter(student=student, classroom=classroom, status=Attendance.Status.ABSENT).count()
        
        percentage = round((present_days / total_days) * 100, 1) if total_days > 0 else 100.0
        is_low_attendance = percentage < 75.0

        report_data.append({
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'percentage': percentage,
            'is_low_attendance': is_low_attendance,
        })

    context = {
        'classroom': classroom,
        'report_data': report_data,
    }
    return render(request, 'academics/attendance_report.html', context)

@login_required
@role_required(User.Role.ADMIN, User.Role.TEACHER)
def character_certificate_view(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    latest_exam = Exam.objects.last()
    marks = Mark.objects.filter(student=student, exam=latest_exam)
    
    total_credits = sum(float(m.subject.credit_hours) for m in marks)
    weighted_gp = sum(m.grade_point * float(m.subject.credit_hours) for m in marks)
    has_ng = any(m.is_ng for m in marks)
    final_gpa = 0.0 if (has_ng or total_credits == 0) else round(weighted_gp / total_credits, 2)

    context = {
        'student': student,
        'final_gpa': final_gpa,
        'issue_date': date.today(),
        'cert_no': f"CC-2081-{student.id:04d}",
    }
    return render(request, 'academics/character_certificate.html', context)