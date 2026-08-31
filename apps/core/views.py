from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.academics.models import ClassRoom, Exam, Subject
from apps.users.models import User

@login_required
def dashboard_view(request):
    classrooms = ClassRoom.objects.all().order_by('name')
    exams = Exam.objects.all().order_by('-date_held')  # Fixed field name here
    subjects = Subject.objects.all().order_by('code')
    students = User.objects.filter(role=User.Role.STUDENT).order_by('username')

    context = {
        'classrooms': classrooms,
        'exams': exams,
        'subjects': subjects,
        'students': students,
    }
    return render(request, 'core/dashboard.html', context)