from edx_shopify.utils import hmac_is_valid, record_order, auto_enroll_email
from django.test import TestCase
from django.http import Http404

from . import JsonPayloadTestCase


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


class RecordOrderTest(JsonPayloadTestCase):

    def test_record_order(self):
        # Make sure the order gets created, and that its ID matches
        # that in the payload
        order1, created1 = record_order(self.json_payload)
        self.assertTrue(created1)
        self.assertEqual(order1.id, self.json_payload['id'])
        # Try to create the order again, make sure we get a reference
        # instead
        order2, created2 = record_order(self.json_payload)
        self.assertFalse(created2)
        self.assertEqual(order1, order2)


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
