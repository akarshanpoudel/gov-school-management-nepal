"""
Object-level permission helpers.

`role_required` (see decorators.py) only checks *which role* a user has.
It does not check *which records* that user is allowed to touch. These
helpers add that second, object-level layer so a TEACHER account is
confined to the classroom(s) they are actually assigned to, and a
STUDENT can only ever see their own records.

Both the ADMIN role and Django superusers are always granted access.
"""

from apps.users.models import User


def is_admin(user):
    """Admins and superusers bypass all object-level restrictions."""
    return user.is_superuser or user.role == User.Role.ADMIN


def can_manage_classroom(user, classroom):
    """
    Can this user take attendance / enter marks / pull reports for this
    classroom? True for admins, and for the TEACHER who is that
    classroom's assigned class_teacher. False for every other teacher
    and for students.
    """
    if is_admin(user):
        return True
    return (
        user.role == User.Role.TEACHER
        and classroom.class_teacher_id is not None
        and classroom.class_teacher_id == user.id
    )


def can_view_student_record(user, student):
    """
    Can this user view a given student's report card / certificate /
    similar personal record? True for admins, the student themselves,
    and the class_teacher of the student's current classroom.
    """
    if is_admin(user):
        return True
    if user.role == User.Role.STUDENT:
        return user.id == student.id
    if user.role == User.Role.TEACHER:
        classroom = getattr(student, 'classroom', None)
        return classroom is not None and classroom.class_teacher_id == user.id
    return False
