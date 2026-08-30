from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import AcademicYear, ClassRoom, Subject, Exam, Mark, Attendance

admin.site.register(AcademicYear)

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'class_teacher')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'academic_year', 'date_held')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credit_hours', 'full_marks_theory', 'full_marks_practical')
    search_fields = ('name', 'code')

@admin.register(Mark)
class MarkAdmin(SimpleHistoryAdmin):
    list_display = ('student', 'exam', 'subject', 'theory_obtained', 'practical_obtained', 'get_total', 'get_grade_point', 'get_ng_status')
    list_filter = ('exam', 'subject')
    
    def get_total(self, obj):
        return obj.total_marks
    get_total.short_description = 'Total'

    def get_grade_point(self, obj):
        return obj.grade_point
    get_grade_point.short_description = 'GP'

    def get_ng_status(self, obj):
        return "NG" if obj.is_ng else "Passed"
    get_ng_status.short_description = 'Status'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'date', 'status', 'remarks')
    list_filter = ('classroom', 'status', 'date')
    search_fields = ('student__username', 'student__first_name', 'student__last_name')