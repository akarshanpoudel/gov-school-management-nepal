from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('marks/entry/<int:exam_id>/<int:subject_id>/', views.mark_entry_view, name='mark_entry'),
]