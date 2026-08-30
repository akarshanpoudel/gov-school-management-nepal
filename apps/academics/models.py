from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords  

class Mark(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    theory_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    practical_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    history = HistoricalRecords()

    class Meta:
        unique_together = ('student', 'exam', 'subject')

    @property
    def is_ng(self):
        if self.theory_obtained < self.subject.pass_marks_theory:
            return True
        if self.practical_obtained < self.subject.pass_marks_practical:
            return True
        return False

    @property
    def total_marks(self):
        return self.theory_obtained + self.practical_obtained

    @property
    def grade_point(self):
        if self.is_ng:
            return 0.0
            
        total_full = self.subject.full_marks_theory + self.subject.full_marks_practical
        percentage = (self.total_marks / total_full) * 100

        if percentage >= 90: return 4.0
        if percentage >= 80: return 3.6
        if percentage >= 70: return 3.2
        if percentage >= 60: return 2.8
        if percentage >= 50: return 2.4
        if percentage >= 40: return 2.0
        if percentage >= 35: return 1.6
        return 0.0

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}: {self.total_marks}"