#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_quartet
------------

Tests for `quartet_epcis` app_models module.
"""

from django.test import TestCase
from django.conf import settings
from tests import test_settings

settings.configure(default_settings=test_settings)


class TestQuartet(TestCase):

    def setUp(self):
        pass

    def test_something(self):
        pass

    def tearDown(self):
        pass
