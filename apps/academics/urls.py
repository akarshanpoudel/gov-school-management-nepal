from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('marks/entry/<int:exam_id>/<int:subject_id>/', views.mark_entry_view, name='mark_entry'),
    path('export/iemis/', views.export_iemis_excel, name='export_iemis'),
    path('export/iemis/xml/', views.export_iemis_xml, name='export_iemis_xml'),
    path('report-card/<int:student_id>/<int:exam_id>/', views.student_report_card_view, name='report_card'),
    path('attendance/entry/<int:classroom_id>/', views.attendance_entry_view, name='attendance_entry'),
    path('attendance/report/<int:classroom_id>/', views.attendance_report_view, name='attendance_report'),
    path('certificate/character/<int:student_id>/', views.character_certificate_view, name='character_certificate'),
]