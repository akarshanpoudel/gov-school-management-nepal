from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('import/', views.bulk_student_import_view, name='bulk_import'),
]