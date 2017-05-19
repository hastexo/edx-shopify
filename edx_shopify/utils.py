import hashlib
import base64
import hmac

from django.core.validators import validate_email
from django.contrib.auth.models import User
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_by_id
from lms.djangoapps.instructor.enrollment import (
    get_user_email_language,
    enroll_email,
    get_email_params
)

from .models import Order


def hmac_is_valid(key, msg, hmac_to_verify):
    hash = hmac.new(str(key), str(msg), hashlib.sha256)
    hmac_calculated = base64.b64encode(hash.digest())
    return hmac.compare_digest(hmac_calculated, hmac_to_verify)


def record_order(data):
    return Order.objects.get_or_create(
        id=data['id'],
        defaults={
            'email': data['customer']['email'],
            'first_name': data['customer']['first_name'],
            'last_name': data['customer']['last_name']
        }
    )


def auto_enroll_email(course_id,
                      email,
                      email_students=False):
    """
    Auto-enroll email in course.

    Based on lms.djangoapps.instructor.views.api.students_update_enrollment()
    """
    # Raises ValidationError if invalid
    validate_email(email)

    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_id)

    # If we want to notify the newly enrolled student by email, fetch
    # the required parameters
    email_params = None
    language = None
    if email_students:
        email_params = get_email_params(course, True, secure=True)

        # Try to find out what language to send the email in.
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            language = get_user_email_language(user)

    # Enroll the email
    enroll_email(course_id,
                 email,
                 auto_enroll=True,
                 email_students=email_students,
                 email_params=email_params,
                 language=language)
