from django.test import TestCase
from django.urls import reverse

from apps.users.models import User


class DashboardRoutingTests(TestCase):
    """Students should always land on their own read-only portal, never the
    staff dashboard that lists every classroom/student in the school."""

    def setUp(self):
        self.student = User.objects.create_user(username='student_a', password='pass1234', role=User.Role.STUDENT)
        self.teacher = User.objects.create_user(username='teacher_a', password='pass1234', role=User.Role.TEACHER)
        self.admin = User.objects.create_user(username='admin1', password='pass1234', role=User.Role.ADMIN)

    def test_student_is_routed_to_student_portal(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(resp, reverse('core:student_dashboard'))

    def test_teacher_sees_staff_dashboard(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse('core:dashboard')).status_code, 200)

    def test_admin_sees_staff_dashboard(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('core:dashboard')).status_code, 200)

    def test_student_cannot_load_staff_dashboard_by_url(self):
        """dashboard_view redirects students away rather than 403ing, since
        it's a benign redirect to their own portal rather than a leak."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse('core:dashboard'), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request['PATH_INFO'], reverse('core:student_dashboard'))
