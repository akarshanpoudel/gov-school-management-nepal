from django.contrib import admin
from .models import AcademicYear, ClassRoom, Subject, Exam, Mark, Attendance

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'class_teacher')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'classroom', 'full_marks', 'is_optional')
    list_filter = ('classroom', 'is_optional')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'academic_year', 'date_held')

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam', 'theory_obtained', 'practical_obtained', 'total_marks', 'is_ng')
    list_filter = ('exam', 'subject__classroom', 'subject')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'date', 'status')
    list_filter = ('classroom', 'status', 'date')