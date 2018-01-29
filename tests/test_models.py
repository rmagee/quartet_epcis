#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_quartet
------------

Tests for `quartet_epcis` app_models module.
"""
import os
import django
import logging

django.setup()
from django.test import TestCase

from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.app_models.EPCIS import entries, events

logger = logging.getLogger(__name__)

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
        self.confirm_agg_event()

    def confirm_parents(self):
        '''
        Makes sure there are two parent entries according
        to the input data
        '''
        res = entries.EntryEvent.objects.filter(is_parent=True)
        self.assertEqual(res.count(), 2, 'There should only be '
                                         'two parent entryevents.')
        logger.debug('Parent count checks out.')

    def confirm_agg_event(self):
        parent = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1')
        entry_event = entries.EntryEvent.objects.get(entry_id=parent.id)
        children = entries.EntryEvent.objects.filter(
            event_id=entry_event.event_id, is_parent=False)
        self.assertEqual(children.count(), 5, 'There should be 5 children '
                                              'for the aggregation event.')
        logger.debug('Aggregation event item count checks out.')
        event = events.Event.objects.get(id=entry_event.event_id)
        self.assertEqual(event.action, 'ADD')



    def tearDown(self):
        pass
