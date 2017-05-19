# -*- coding: utf-8 -*-
import json
import os

from django.test import TestCase


class JsonPayloadTestCase(TestCase):

    def setUp(self):
        # Grab an example payload and make it available to test
        # methods as a raw string and as a JSON dictionary.
        payload_file = os.path.join(os.path.dirname(__file__),
                                    'post.json')
        self.raw_payload = open(payload_file, 'r').read()
        self.json_payload = json.loads(self.raw_payload)
