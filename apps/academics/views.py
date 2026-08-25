from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Exam, Subject, Mark
from apps.users.models import User

def is_teacher_or_admin(user):
    return user.is_authenticated and user.role in [User.Role.ADMIN, User.Role.TEACHER]

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
                
                # update_or_create ensures we don't duplicate records on re-submission
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