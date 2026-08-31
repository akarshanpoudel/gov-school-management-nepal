from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from apps.academics.models import Exam, ClassRoom

@login_required
def dashboard_view(request):
    students = User.objects.filter(role=User.Role.STUDENT)
    latest_exam = Exam.objects.last()
    classrooms = ClassRoom.objects.all()
    
    context = {
        'students': students,
        'latest_exam': latest_exam,
        'classrooms': classrooms,
    }
    return render(request, 'core/dashboard.html', context)