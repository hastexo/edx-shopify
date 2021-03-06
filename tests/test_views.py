# -*- coding: utf-8 -*-
import hashlib
import base64
import hmac

from django.conf import settings
from django.test import Client

# We need this in order to mock.patch get_course_by_id
from edx_shopify import utils

from . import ShopifyTestCase

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


class TestOrderCreation(ShopifyTestCase):

    def setUp(self):
        self.setup_payload()

        # Set enforce_csrf_checks=True here because testing must still
        # work (webhooks are explicitly exempted from CSRF protection)
        self.client = Client(enforce_csrf_checks=True)

        conf = settings.WEBHOOK_SETTINGS['edx_shopify']

        # Calculate 3 SHA256 hashes over the payload, which the
        # webhook handler must verify and accept or reject: a correct
        # hash, a hash from the wrong (reversed) key, and a corrupted
        # hash containing an invalid base64 character.
        correct_hash = hmac.new(conf['api_key'],
                                self.raw_payload,
                                hashlib.sha256)
        incorrect_hash = hmac.new(conf['api_key'][::-1],
                                  self.raw_payload,
                                  hashlib.sha256)
        self.correct_signature = base64.b64encode(correct_hash.digest())
        self.incorrect_signature = base64.b64encode(incorrect_hash.digest())
        self.corrupt_signature = "-%s" % base64.b64encode(correct_hash.digest())[1:]  # noqa: E501

        # Set up a mock course
        self.setup_course()

    def test_invalid_method_put(self):
        response = self.client.put('/shopify/order/create',
                                   self.raw_payload,
                                   content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def test_invalid_method_get(self):
        response = self.client.get('/shopify/order/create')
        self.assertEqual(response.status_code, 405)

    def test_missing_headers(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_incorrect_signature(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json',
                                    HTTP_X_SHOPIFY_HMAC_SHA256=self.incorrect_signature,  # noqa: E501
                                    HTTP_X_SHOPIFY_SHOP_DOMAIN='example.com')
        self.assertEqual(response.status_code, 403)

    def test_corrupt_signature(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json',
                                    HTTP_X_SHOPIFY_HMAC_SHA256=self.corrupt_signature,  # noqa: E501
                                    HTTP_X_SHOPIFY_SHOP_DOMAIN='example.com')
        self.assertEqual(response.status_code, 403)

    def test_invalid_domain(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json',
                                    HTTP_X_SHOPIFY_HMAC_SHA256=self.correct_signature,  # noqa: E501
                                    HTTP_X_SHOPIFY_SHOP_DOMAIN='nonexistant-domain.com')  # noqa: E501
        self.assertEqual(response.status_code, 403)

    def test_valid_order(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json',
                                    HTTP_X_SHOPIFY_HMAC_SHA256=self.correct_signature,  # noqa: E501
                                    HTTP_X_SHOPIFY_SHOP_DOMAIN='example.com')

        mock_get_course_by_id = Mock(return_value=self.course)
        mock_get_email_params = Mock(return_value=self.email_params)
        mock_enroll_email = Mock()
        with patch.multiple(utils,
                            get_course_by_id=mock_get_course_by_id,
                            get_email_params=mock_get_email_params,
                            enroll_email=mock_enroll_email):
            self.assertEqual(response.status_code, 200)
