from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.exceptions import ValidationError


def _lockout_cache_key(username):
    return f'login-attempts:{username.lower()}'


class ThrottledAuthenticationForm(AuthenticationForm):
    """
    Locks a *username* out after settings.LOGIN_ATTEMPT_LIMIT consecutive
    failed attempts, for settings.LOGIN_ATTEMPT_TIMEOUT_SECONDS.

    The README claims "Automated IP throttling and failed-login lockouts"
    but no such mechanism existed in the code. This closes that gap without
    adding a new dependency (e.g. django-axes) using Django's built-in
    cache framework. The counter is keyed by username rather than IP, so
    the lockout can't be bypassed by an attacker rotating source IPs.

    In production, back CACHES with Redis or Memcached rather than the
    default per-process LocMemCache, otherwise each Gunicorn worker tracks
    its own counter and the effective limit becomes (limit * worker count).
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        'locked_out': (
            "Too many failed login attempts for this account. "
            "Please try again in %(minutes)d minute(s)."
        ),
    }

    def clean(self):
        username = self.cleaned_data.get('username')

        if username:
            key = _lockout_cache_key(username)
            if cache.get(key, 0) >= settings.LOGIN_ATTEMPT_LIMIT:
                minutes = max(1, settings.LOGIN_ATTEMPT_TIMEOUT_SECONDS // 60)
                raise ValidationError(
                    self.error_messages['locked_out'],
                    code='locked_out',
                    params={'minutes': minutes},
                )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            if username:
                key = _lockout_cache_key(username)
                cache.set(key, cache.get(key, 0) + 1, settings.LOGIN_ATTEMPT_TIMEOUT_SECONDS)
            raise

        if username:
            cache.delete(_lockout_cache_key(username))

        return cleaned_data
