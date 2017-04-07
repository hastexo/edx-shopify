import hashlib, base64, hmac

from django.core.validators import validate_email
from django.contrib.auth.models import User
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_by_id
from lms.djangoapps.instructor.enrollment import (
    get_user_email_language,
    enroll_email,
    get_email_params
)

def hmac_is_valid(key, msg, hmac_to_verify):
    hash = hmac.new(key, msg, hashlib.sha256)
    hmac_calculated = base64.b64encode(hash.digest())
    return hmac_calculated == hmac_to_verify

def auto_enroll_email(course_id, email):
    """
    Auto-enroll email in course.

    Based on lms.djangoapps.instructor.views.api.students_update_enrollment()
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_id)
    email_params = get_email_params(course, True, secure=True)

    # Raises ValidationError if invalid
    validate_email(email)

    # Try to find out what language to send the email in.
    user = None
    language = None
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        pass
    else:
        language = get_user_email_language(user)

    # Enroll the email
    enroll_email(course_id, email, True, True, email_params, language=language)
