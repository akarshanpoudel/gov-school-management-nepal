from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('marks/entry/<int:exam_id>/<int:subject_id>/', views.mark_entry_view, name='mark_entry'),
    path('export/iemis/', views.export_iemis_excel, name='export_iemis'), # <-- ADD THIS ROUTE
]