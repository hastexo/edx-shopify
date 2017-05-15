# -*- coding: utf-8 -*-
import json
import os
import hashlib
import base64
import hmac

from django.conf import settings
from django.test import TestCase, Client
from edx_shopify.models import Order


class TestOrderCreation(TestCase):

    def setUp(self):
        # Set enforce_csrf_checks=True here because testing must still
        # work (webhooks are explicitly exempted from CSRF protection)
        self.client = Client(enforce_csrf_checks=True)

        conf = settings.WEBHOOK_SETTINGS['edx_shopify']

        # Grab an example payload and make it available to test
        # methods as a raw string and as a JSON dictionary.
        payload_file = os.path.join(os.path.dirname(__file__),
                                    'post.json')
        self.raw_payload = open(payload_file, 'r').read()
        self.json_payload = json.loads(self.raw_payload)

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

    def test_successful_order_creation(self):
        response = self.client.post('/shopify/order/create',
                                    self.raw_payload,
                                    content_type='application/json',
                                    HTTP_X_SHOPIFY_HMAC_SHA256=self.correct_signature,  # noqa: E501
                                    HTTP_X_SHOPIFY_SHOP_DOMAIN='example.com')
        self.assertEqual(response.status_code, 200)

        order = Order.objects.get(id=self.json_payload['id'])
        self.assertEqual(order.email,
                         self.json_payload['customer']['email'])
        self.assertEqual(order.first_name,
                         self.json_payload['customer']['first_name'])
        self.assertEqual(order.last_name,
                         self.json_payload['customer']['last_name'])

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
