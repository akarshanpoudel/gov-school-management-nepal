from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import ClassRoom
from apps.users.models import User
from apps.users.permissions import is_admin, can_manage_classroom, can_view_student_record


class PermissionHelperTests(TestCase):
    """Unit tests for the object-level RBAC helpers in apps/users/permissions.py."""

    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='x', role=User.Role.ADMIN)
        self.superuser = User.objects.create_superuser(username='root', password='x', email='root@example.com')
        self.teacher_a = User.objects.create_user(username='teacher_a', password='x', role=User.Role.TEACHER)
        self.teacher_b = User.objects.create_user(username='teacher_b', password='x', role=User.Role.TEACHER)
        self.classroom = ClassRoom.objects.create(name='Grade 10', class_teacher=self.teacher_a)
        self.unassigned_classroom = ClassRoom.objects.create(name='Grade 8')
        self.student = User.objects.create_user(
            username='student_a', password='x', role=User.Role.STUDENT, classroom=self.classroom
        )
        self.other_student = User.objects.create_user(username='student_b', password='x', role=User.Role.STUDENT)

    def test_is_admin(self):
        self.assertTrue(is_admin(self.admin))
        self.assertTrue(is_admin(self.superuser))
        self.assertFalse(is_admin(self.teacher_a))
        self.assertFalse(is_admin(self.student))

    def test_can_manage_classroom(self):
        self.assertTrue(can_manage_classroom(self.admin, self.classroom))
        self.assertTrue(can_manage_classroom(self.teacher_a, self.classroom))
        self.assertFalse(can_manage_classroom(self.teacher_b, self.classroom))
        self.assertFalse(can_manage_classroom(self.student, self.classroom))

    def test_can_manage_classroom_with_no_assigned_teacher(self):
        self.assertFalse(can_manage_classroom(self.teacher_a, self.unassigned_classroom))
        self.assertTrue(can_manage_classroom(self.admin, self.unassigned_classroom))

    def test_can_view_student_record(self):
        self.assertTrue(can_view_student_record(self.admin, self.student))
        self.assertTrue(can_view_student_record(self.student, self.student))
        self.assertFalse(can_view_student_record(self.other_student, self.student))
        self.assertTrue(can_view_student_record(self.teacher_a, self.student))
        self.assertFalse(can_view_student_record(self.teacher_b, self.student))

    def test_can_view_student_record_with_no_classroom(self):
        self.assertFalse(can_view_student_record(self.teacher_a, self.other_student))
        self.assertTrue(can_view_student_record(self.admin, self.other_student))


class BulkImportTests(TestCase):
    """
    Regression coverage: bulk_student_import_view used to give every new
    student the same hardcoded password ('student123'), so any account's
    password was guessable from the source code. Passwords must now be
    random and distinct per student.
    """

    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='pass1234', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher_a', password='pass1234', role=User.Role.TEACHER)
        self.classroom = ClassRoom.objects.create(name='Grade 10')

    def _upload(self, csv_content):
        f = SimpleUploadedFile('students.csv', csv_content.encode(), content_type='text/csv')
        return self.client.post(reverse('users:bulk_import'), {'csv_file': f})

    def test_non_admin_forbidden(self):
        self.client.force_login(self.teacher)
        resp = self._upload('username,first_name,last_name,classroom\nSTU-1,A,B,Grade 10\n')
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(User.objects.filter(username='STU-1').exists())

    def test_imported_students_get_distinct_random_passwords(self):
        self.client.force_login(self.admin)
        self._upload(
            'username,first_name,last_name,classroom\n'
            'STU-BULK-1,Aarav,Sharma,Grade 10\n'
            'STU-BULK-2,Bina,Thapa,Grade 10\n'
        )

        u1 = User.objects.get(username='STU-BULK-1')
        u2 = User.objects.get(username='STU-BULK-2')

        self.assertFalse(u1.check_password('student123'))
        self.assertFalse(u2.check_password('student123'))
        self.assertNotEqual(u1.password, u2.password)
        self.assertEqual(u1.role, User.Role.STUDENT)
        self.assertEqual(u1.classroom_id, self.classroom.id)

    def test_existing_username_is_not_recreated_or_repassworded(self):
        existing = User.objects.create_user(
            username='STU-EXISTING', password='OriginalPass1', role=User.Role.STUDENT
        )
        self.client.force_login(self.admin)
        self._upload('username,first_name,last_name,classroom\nSTU-EXISTING,A,B,Grade 10\n')

        existing.refresh_from_db()
        self.assertTrue(existing.check_password('OriginalPass1'))


class LoginThrottleTests(TestCase):
    """
    Regression coverage for two auth bugs:
    1. LOGIN_URL previously pointed at /admin/login/, which rejects any
       non-staff user even with a correct password.
    2. The README claimed brute-force lockout existed; nothing enforced it.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='stu_login', password='CorrectPass123', role=User.Role.STUDENT)

    def tearDown(self):
        cache.clear()

    def test_anonymous_user_redirected_to_app_login_not_admin(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/login/'))

    def test_correct_credentials_log_in_successfully(self):
        resp = self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'CorrectPass123'})
        self.assertEqual(resp.status_code, 302)

    def test_lockout_after_repeated_failures(self):
        from django.conf import settings

        for _ in range(settings.LOGIN_ATTEMPT_LIMIT):
            self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'wrong'})

        # Even the *correct* password is now rejected until the window expires.
        resp = self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'CorrectPass123'})
        self.assertContains(resp, 'Too many failed login attempts', status_code=200)

    def test_successful_login_resets_the_failure_counter(self):
        from django.conf import settings

        # One failure short of the limit, then succeed.
        for _ in range(settings.LOGIN_ATTEMPT_LIMIT - 1):
            self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'wrong'})
        resp = self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'CorrectPass123'})
        self.assertEqual(resp.status_code, 302)

        # Counter should be cleared, so a fresh run of failures starts from zero.
        self.client.post(reverse('logout'))
        for _ in range(settings.LOGIN_ATTEMPT_LIMIT - 1):
            resp = self.client.post(reverse('login'), {'username': 'stu_login', 'password': 'wrong'})
        self.assertNotContains(resp, 'Too many failed login attempts', status_code=200)
