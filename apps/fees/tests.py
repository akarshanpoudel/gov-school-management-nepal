from django.test import TestCase
from django.urls import reverse

from apps.users.models import User
from apps.academics.models import AcademicYear, ClassRoom, Exam, Subject, Mark
from apps.fees.models import Invoice


class FeesFixtureMixin:
    """
    An admin, a teacher, and a student with one invoice. Every view in
    apps/fees/views.py touches every student's financial records or can
    mutate academic standing (promotion), so all three should be ADMIN-only.
    """

    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='pass1234', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher_a', password='pass1234', role=User.Role.TEACHER)

        self.academic_year = AcademicYear.objects.create(title='2081 BS', is_active=True)
        self.classroom = ClassRoom.objects.create(name='Grade 10', section='A', class_teacher=self.teacher)
        self.student = User.objects.create_user(
            username='student_a', password='pass1234', role=User.Role.STUDENT, classroom=self.classroom
        )

        self.invoice = Invoice.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            title='Term Fee',
            due_date='2026-03-01',
            total_amount=1000,
        )


class FeeDashboardAccessTests(FeesFixtureMixin, TestCase):
    """
    Regression coverage: fee_dashboard_view previously had no role check at
    all, so any logged-in student could see every student's invoices and
    the school-wide totals. The nav only *hides* the link for non-admins;
    it never enforced anything server-side.
    """

    def test_student_forbidden(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('fees:dashboard')).status_code, 403)

    def test_teacher_forbidden(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse('fees:dashboard')).status_code, 403)

    def test_admin_allowed(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('fees:dashboard')).status_code, 200)


class RecordPaymentAccessTests(FeesFixtureMixin, TestCase):
    """
    Regression coverage: record_payment_view previously had no role check,
    so a student could POST to their own (or anyone else's) invoice and
    mark it paid without actually paying, or tamper with someone else's
    balance.
    """

    def _url(self):
        return reverse('fees:record_payment', args=[self.invoice.id])

    def test_student_cannot_view_payment_form(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_student_cannot_record_a_payment(self):
        self.client.force_login(self.student)
        resp = self.client.post(self._url(), {'amount': '1000'})
        self.assertEqual(resp.status_code, 403)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, 0)
        self.assertEqual(self.invoice.status, Invoice.Status.UNPAID)

    def test_admin_can_record_a_payment(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self._url(), {'amount': '500'})
        self.assertEqual(resp.status_code, 302)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, 500)
        self.assertEqual(self.invoice.status, Invoice.Status.PARTIAL)


class StudentPromotionAccessTests(FeesFixtureMixin, TestCase):
    """
    Regression coverage: student_promotion_view previously had no role
    check, so any authenticated user could trigger bulk grade promotion or
    graduation for an entire classroom.
    """

    def setUp(self):
        super().setUp()
        self.target_classroom = ClassRoom.objects.create(name='Grade 11', section='A')

    def _url(self):
        return reverse('fees:promotion')

    def test_student_cannot_trigger_promotion(self):
        self.client.force_login(self.student)
        resp = self.client.post(self._url(), {
            'source_class': self.classroom.id,
            'target_class': self.target_classroom.id,
        })
        self.assertEqual(resp.status_code, 403)

        self.student.refresh_from_db()
        self.assertEqual(self.student.classroom_id, self.classroom.id)

    def test_admin_can_promote_a_passing_student(self):
        # No Mark records for the latest exam => no NG marks => qualifies.
        Exam.objects.create(academic_year=self.academic_year, title='First Terminal', date_held='2026-01-15')

        self.client.force_login(self.admin)
        resp = self.client.post(self._url(), {
            'source_class': self.classroom.id,
            'target_class': self.target_classroom.id,
        })
        self.assertEqual(resp.status_code, 302)

        self.student.refresh_from_db()
        self.assertEqual(self.student.classroom_id, self.target_classroom.id)

    def test_admin_promotion_skips_students_with_a_failing_grade(self):
        exam = Exam.objects.create(academic_year=self.academic_year, title='First Terminal', date_held='2026-01-15')
        subject = Subject.objects.create(name='Math', classroom=self.classroom)
        # Below pass_marks_theory (27.0 default) -> is_ng True -> should not be promoted.
        Mark.objects.create(student=self.student, exam=exam, subject=subject, theory_obtained=5, practical_obtained=5)

        self.client.force_login(self.admin)
        self.client.post(self._url(), {
            'source_class': self.classroom.id,
            'target_class': self.target_classroom.id,
        })

        self.student.refresh_from_db()
        self.assertEqual(self.student.classroom_id, self.classroom.id)
