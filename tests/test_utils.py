from django.test import TestCase
from django.http import Http404
from django.core.exceptions import ValidationError

from edx_shopify.utils import hmac_is_valid, record_order
from edx_shopify.utils import auto_enroll_email, process_line_item

from edx_shopify.models import Order

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


class ProcessLineItemTest(TestCase):

    def test_invalid_line_item(self):
        order = Order()
        order.id = 41
        order.save()
        line_items = [{"sku": "course-v1:org+nosuchcourse+run1"},
                      {"properties": [{"name": "email",
                                       "value": "learner@example.com"}]}]
        for line_item in line_items:
            with self.assertRaises(KeyError):
                process_line_item(order, line_item)

    def test_invalid_sku(self):
        order = Order()
        order.id = 42
        order.save()
        line_items = [{"properties": [{"name": "email",
                                       "value": "learner@example.com"}],
                       "sku": "course-v1:org+nosuchcourse+run1"}]
        for line_item in line_items:
            with self.assertRaises(Http404):
                process_line_item(order, line_item)

    def test_invalid_email(self):
        order = Order()
        order.id = 43
        order.save()
        line_items = [{"properties": [{"name": "email",
                                       "value": "akjzcdfbgakugbfvkljzgh"}],
                       "sku": "course-v1:org+course+run1"}]
        for line_item in line_items:
            with self.assertRaises(ValidationError):
                process_line_item(order, line_item)


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
