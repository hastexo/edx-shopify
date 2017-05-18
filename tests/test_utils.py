from edx_shopify.utils import hmac_is_valid, auto_enroll_email
from django.test import TestCase
from django.http import Http404


class SignatureVerificationTest(TestCase):

    def test_hmac_is_valid(self):
        correct_hmac = [
            ('hello', 'world', '8ayXAutfryPKKRpNxG3t3u4qeMza8KQSvtdxTP/7HMQ='),
            ('bye', 'bye', 'HHfaL+C4HxPTexmlKO9pwEHuAXkErAz85APGPOgvBVU='),
            ('foo', 'bar', '+TILrwJJFp5zhQzWFW3tAQbiu2rYyrAbe7vr5tEGUxc=')
        ]

        incorrect_hmac = [
            ('hello', 'world', '+TILrwJJFp5zhQzWFW3tAQbiu2rYyrAbe7vr5tEGUxc='),
            ('bye', 'bye', '8ayXAutfryPKKRpNxG3t3u4qeMza8KQSvtdxTP/7HMQ='),
            ('foo', 'bar', 'HHfaL+C4HxPTexmlKO9pwEHuAXkErAz85APGPOgvBVU=')
        ]

        for triplet in correct_hmac:
            self.assertTrue(hmac_is_valid(*triplet))

        for triplet in incorrect_hmac:
            self.assertFalse(hmac_is_valid(*triplet))


class EmailEnrollmentTest(TestCase):

    def test_enrollment_failure(self):
        # Enrolling in a non-existent course (or run) should fail, no
        # matter whether the user exists or not
        with self.assertRaises(Http404):
            auto_enroll_email('course-v1:org+nosuchcourse+run1',
                              'learner@example.com')
            auto_enroll_email('course-v1:org+course+nosuchrun',
                              'learner@example.com')
            auto_enroll_email('course-v1:org+nosuchcourse+run1',
                              'johndoe@example.com')
