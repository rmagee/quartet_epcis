#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_quartet
------------

Tests for `quartet_epcis` app_models module.
"""
import os
import django
django.setup()
from django.test import TestCase

from quartet_epcis.parsing.parser import QuartetParser



class TestQuartet(TestCase):
    def setUp(self):
        pass

    def test_something(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        parser.parse()
        print(parser.event_cache)
        parser.clear_cache()

    def tearDown(self):
        pass
