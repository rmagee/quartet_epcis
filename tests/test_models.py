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
from quartet_epcis.app_models.EPCIS.entries import EntryEvent



class TestQuartet(TestCase):
    def setUp(self):
        pass

    def test_a_epcis_parser(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        self.confirm_parents()

    def confirm_parents(self):
        '''
        Makes sure there are two parent entries according
        to the input data
        '''
        res = EntryEvent.objects.filter(is_parent=True)
        print(res)
        self.assertEqual(res.count(),2,'There should only be '
                                       'two parent entryevents.')


    def tearDown(self):
        pass
