import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Exam, Subject, Mark
from apps.users.models import User

def is_teacher_or_admin(user):
    return user.is_authenticated and user.role in [User.Role.ADMIN, User.Role.TEACHER]

def is_admin_or_staff(user):
    return user.is_authenticated and user.role in [User.Role.ADMIN, User.Role.STAFF]

@login_required
@user_passes_test(is_teacher_or_admin)
def mark_entry_view(request, exam_id, subject_id):
    exam = get_object_or_404(Exam, id=exam_id)
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Fetch all students
    students = User.objects.filter(role=User.Role.STUDENT).order_by('username')
    
    if request.method == 'POST':
        for student in students:
            theory_key = f'theory_{student.id}'
            practical_key = f'practical_{student.id}'
            
            if theory_key in request.POST and practical_key in request.POST:
                theory_val = request.POST.get(theory_key) or 0
                practical_val = request.POST.get(practical_key) or 0
                
                # update_or_create ensures no duplicate records on re-submission
                Mark.objects.update_or_create(
                    student=student,
                    exam=exam,
                    subject=subject,
                    defaults={
                        'theory_obtained': theory_val,
                        'practical_obtained': practical_val
                    }
                )
        return redirect('academics:mark_entry', exam_id=exam.id, subject_id=subject.id)

    # PRE-FETCH TO AVOID N+1 QUERIES: Map student_id to their Mark object
    existing_marks = {
        mark.student_id: mark for mark in Mark.objects.filter(exam=exam, subject=subject)
    }

    context = {
        'exam': exam,
        'subject': subject,
        'students': students,
        'existing_marks': existing_marks,
    }
    return render(request, 'academics/mark_entry.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def export_iemis_excel(request):
    """
    Queries student demographic data and outputs a formatted Excel file 
    matching CEHRD / IEMIS bulk upload column specifications.
    """
    students = User.objects.filter(role=User.Role.STUDENT).values(
        'username', 
        'first_name', 
        'last_name', 
        'citizenship_no', 
        'phone_number',
        'created_at'
    )
    
    df = pd.DataFrame(list(students))
    
    if not df.empty:
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d')

        df.rename(columns={
            'username': 'IEMIS Student ID / Roll',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'citizenship_no': 'Citizenship / Birth Reg No.',
            'phone_number': 'Guardian Contact',
            'created_at': 'Registration Date (AD)'
        }, inplace=True)
    else:
        df = pd.DataFrame(columns=[
            'IEMIS Student ID / Roll', 'First Name', 'Last Name', 
            'Citizenship / Birth Reg No.', 'Guardian Contact', 'Registration Date (AD)'
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="CEHRD_IEMIS_Student_Export_2081.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Student_Baseline_Data')

    return response