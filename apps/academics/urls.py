from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('marks/entry/<int:classroom_id>/<int:subject_id>/<int:exam_id>/', views.mark_entry_view, name='mark_entry'),
    path('attendance/entry/<int:classroom_id>/', views.attendance_entry_view, name='attendance_entry'),
    path('report-card/<int:student_id>/<int:exam_id>/', views.report_card_view, name='report_card'),
    path('character-certificate/<int:student_id>/', views.character_certificate_view, name='character_certificate'),
    path('attendance/report/<int:classroom_id>/', views.attendance_report_view, name='attendance_report'),
    
    # IEMIS Exports
    path('export/iemis/', views.export_iemis_view, name='export_iemis'),
    path('export/iemis/csv/', views.export_iemis_view, name='export_iemis_csv'),
    path('export/iemis/xml/', views.export_iemis_xml_view, name='export_iemis_xml'),
]