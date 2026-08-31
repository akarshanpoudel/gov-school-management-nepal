from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('student/portal/', views.student_dashboard_view, name='student_dashboard'),
]