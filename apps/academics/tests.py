from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.users.models import User
from apps.academics.models import AcademicYear, ClassRoom, Subject, Exam, Mark
from apps.academics.views import get_grade_info


class GradeInfoTests(TestCase):
    """CDC (Curriculum Development Centre) letter-grade / GPA boundaries."""

    def test_grade_boundaries(self):
        cases = [
            (100, 'A+', 4.0),
            (90, 'A+', 4.0),
            (89.99, 'A', 3.6),
            (80, 'A', 3.6),
            (79.99, 'B+', 3.2),
            (70, 'B+', 3.2),
            (69.99, 'B', 2.8),
            (60, 'B', 2.8),
            (59.99, 'C+', 2.4),
            (50, 'C+', 2.4),
            (49.99, 'C', 2.0),
            (40, 'C', 2.0),
            (39.99, 'D', 1.6),
            (35, 'D', 1.6),
            (34.99, 'NG', 0.0),
            (0, 'NG', 0.0),
        ]
        for pct, expected_grade, expected_gpa in cases:
            with self.subTest(pct=pct):
                grade, gpa = get_grade_info(pct)
                self.assertEqual(grade, expected_grade)
                self.assertEqual(gpa, expected_gpa)


class AcademicFixtureMixin:
    """
    Two classrooms, each with its own class_teacher, one subject on
    classroom_a, one student per classroom, and a shared exam. Used by every
    test class below so classroom-scoped RBAC can be exercised the same way
    the earlier manual testing did (teacher_a is assigned to classroom_a,
    teacher_b to classroom_b; neither should be able to touch the other's
    classroom).
    """

    def setUp(self):
        self.academic_year = AcademicYear.objects.create(title='2081 BS', is_active=True)
        self.exam = Exam.objects.create(
            academic_year=self.academic_year, title='First Terminal', date_held=date(2026, 1, 15)
        )

        self.teacher_a = User.objects.create_user(username='teacher_a', password='pass1234', role=User.Role.TEACHER)
        self.teacher_b = User.objects.create_user(username='teacher_b', password='pass1234', role=User.Role.TEACHER)
        self.admin = User.objects.create_user(username='admin1', password='pass1234', role=User.Role.ADMIN)

        self.classroom_a = ClassRoom.objects.create(name='Grade 10', section='A', class_teacher=self.teacher_a)
        self.classroom_b = ClassRoom.objects.create(name='Grade 9', section='B', class_teacher=self.teacher_b)

        self.subject = Subject.objects.create(name='Science', classroom=self.classroom_a)

        self.student_a = User.objects.create_user(
            username='student_a', password='pass1234', role=User.Role.STUDENT, classroom=self.classroom_a
        )
        self.student_b = User.objects.create_user(
            username='student_b', password='pass1234', role=User.Role.STUDENT, classroom=self.classroom_b
        )


class MarkEntryAccessTests(AcademicFixtureMixin, TestCase):
    def _url(self):
        return reverse('academics:mark_entry', args=[self.classroom_a.id, self.subject.id, self.exam.id])

    def test_assigned_class_teacher_can_access(self):
        self.client.force_login(self.teacher_a)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_other_teacher_is_forbidden(self):
        """teacher_b is not classroom_a's class_teacher and must be blocked."""
        self.client.force_login(self.teacher_b)
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_admin_can_access_any_classroom(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_student_is_forbidden(self):
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_anonymous_user_is_redirected_to_app_login(self):
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)


class MarkEntrySavingTests(AcademicFixtureMixin, TestCase):
    """
    Regression coverage for the theory_marks/practical_marks FieldError bug:
    Mark.theory_marks / practical_marks are read-only @property aliases, not
    real fields. Saving must go through theory_obtained / practical_obtained.
    """

    def _url(self):
        return reverse('academics:mark_entry', args=[self.classroom_a.id, self.subject.id, self.exam.id])

    def test_posting_marks_persists_successfully(self):
        self.client.force_login(self.teacher_a)
        resp = self.client.post(self._url(), {
            f'theory_{self.student_a.id}': '60',
            f'practical_{self.student_a.id}': '20',
        })
        self.assertEqual(resp.status_code, 302)

        mark = Mark.objects.get(student=self.student_a, subject=self.subject, exam=self.exam)
        self.assertEqual(float(mark.theory_obtained), 60.0)
        self.assertEqual(float(mark.practical_obtained), 20.0)
        self.assertEqual(float(mark.total_marks), 80.0)

    def test_resubmitting_updates_existing_mark_instead_of_erroring(self):
        self.client.force_login(self.teacher_a)
        self.client.post(self._url(), {
            f'theory_{self.student_a.id}': '40',
            f'practical_{self.student_a.id}': '10',
        })
        self.client.post(self._url(), {
            f'theory_{self.student_a.id}': '55',
            f'practical_{self.student_a.id}': '15',
        })

        self.assertEqual(Mark.objects.filter(student=self.student_a, subject=self.subject, exam=self.exam).count(), 1)
        mark = Mark.objects.get(student=self.student_a, subject=self.subject, exam=self.exam)
        self.assertEqual(float(mark.theory_obtained), 55.0)
        self.assertEqual(float(mark.practical_obtained), 15.0)

    def test_marks_above_subject_maximum_are_rejected(self):
        self.client.force_login(self.teacher_a)
        resp = self.client.post(self._url(), {
            # subject.full_marks_theory defaults to 75.0
            f'theory_{self.student_a.id}': '999',
            f'practical_{self.student_a.id}': '20',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            Mark.objects.filter(student=self.student_a, subject=self.subject, exam=self.exam).exists()
        )

    def test_negative_marks_are_rejected(self):
        self.client.force_login(self.teacher_a)
        self.client.post(self._url(), {
            f'theory_{self.student_a.id}': '-5',
            f'practical_{self.student_a.id}': '10',
        })
        self.assertFalse(
            Mark.objects.filter(student=self.student_a, subject=self.subject, exam=self.exam).exists()
        )


class AttendanceAccessTests(AcademicFixtureMixin, TestCase):
    def test_assigned_class_teacher_can_enter_attendance(self):
        self.client.force_login(self.teacher_a)
        resp = self.client.get(reverse('academics:attendance_entry', args=[self.classroom_a.id]))
        self.assertEqual(resp.status_code, 200)

    def test_other_teacher_forbidden_from_attendance_entry(self):
        self.client.force_login(self.teacher_b)
        resp = self.client.get(reverse('academics:attendance_entry', args=[self.classroom_a.id]))
        self.assertEqual(resp.status_code, 403)

    def test_assigned_class_teacher_can_view_attendance_report(self):
        self.client.force_login(self.teacher_a)
        resp = self.client.get(reverse('academics:attendance_report', args=[self.classroom_a.id]))
        self.assertEqual(resp.status_code, 200)

    def test_other_teacher_forbidden_from_attendance_report(self):
        self.client.force_login(self.teacher_b)
        resp = self.client.get(reverse('academics:attendance_report', args=[self.classroom_a.id]))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_access_any_classrooms_attendance(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('academics:attendance_entry', args=[self.classroom_a.id]))
        self.assertEqual(resp.status_code, 200)


class ReportCardAccessTests(AcademicFixtureMixin, TestCase):
    """Regression coverage for the report-card IDOR: any authenticated user
    could previously view any student's report card by changing the URL."""

    def _url(self, student):
        return reverse('academics:report_card', args=[student.id, self.exam.id])

    def test_student_can_view_own_report_card(self):
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 200)

    def test_student_cannot_view_another_students_report_card(self):
        self.client.force_login(self.student_b)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 403)

    def test_assigned_class_teacher_can_view_their_students_report_card(self):
        self.client.force_login(self.teacher_a)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 200)

    def test_other_teacher_cannot_view_report_card(self):
        self.client.force_login(self.teacher_b)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 403)

    def test_admin_can_view_any_report_card(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 200)


class CharacterCertificateAccessTests(AcademicFixtureMixin, TestCase):
    def _url(self, student):
        return reverse('academics:character_certificate', args=[student.id])

    def test_student_can_view_own_certificate(self):
        self.client.force_login(self.student_a)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 200)

    def test_student_cannot_view_another_students_certificate(self):
        self.client.force_login(self.student_b)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 403)

    def test_admin_can_view_any_certificate(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self._url(self.student_a)).status_code, 200)
