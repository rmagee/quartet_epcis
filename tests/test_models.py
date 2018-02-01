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
from EPCPyYes.core.v1_2.CBV import business_steps, business_transactions, \
    dispositions
from EPCPyYes.core.v1_2.events import Action
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.app_models.EPCIS import entries, events, choices

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
        self.confirm_transaction_event()
        self.confirm_object_event()
        self.confirm_transformation_event()

    def test_b_caches(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml'),
            event_cache_size=2
        )
        parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        self.confirm_parents()
        self.confirm_agg_event()
        self.confirm_transaction_event()
        self.confirm_object_event()
        self.confirm_transformation_event()

    def confirm_parents(self):
        '''
        Makes sure there are two parent entries according
        to the input data
        '''
        res = entries.EntryEvent.objects.filter(is_parent=True)
        self.assertEqual(res.count(), 2, 'There should only be '
                                         'two parent entryevents.')
        logger.debug('Parent count checks out.')
        self.confirm_two_parents()

    def confirm_object_event(self):
        item = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.0555555.1',
        )
        entry_events = entries.EntryEvent.objects.filter(
            identifier=item.identifier
        ).values_list('event_id')
        event = events.Event.objects.filter(
            id__in=entry_events,
            type=choices.EventTypeChoicesEnum.OBJECT.value
        )
        self.assertEqual(event.count(), 1, "There should only be one "
                                           "object event.")
        # make sure there are 5 epcs for this event
        event = event[0]
        serials = entries.EntryEvent.objects.filter(
            event_id=event.id
        )
        self.assertEqual(serials.count(), 5,
                         'There should be five entry events'
                         'for this event id.')
        self.check_sglns(event)
        self.get_biz_transactions(event)
        self.get_source_destination(event)
        self.assertEqual(event.action, Action.add.value)

    def confirm_transformation_event(self):
        entry_event = entries.EntryEvent.objects.prefetch_related().get(
            identifier='urn:epc:id:sgtin:305555.1555555.2000')
        event = entry_event.event

        bizxact = events.BusinessTransaction.objects.filter(event_id=event.id)
        self.assertEqual(bizxact.count(), 2, 'There should be 2 biz '
                                             'transactions for this event.')
        self.assertEqual(
            bizxact[0].type,
            business_transactions.BusinessTransactionType.Despatch_Advice.value,
            'the business transaction type is not correct.')
        self.assertEqual(bizxact[0].biz_transaction,
                         'urn:epcglobal:cbv:bt:0555555555555.DE45_111')

        self.check_sglns(event)
        self.get_source_destination(event)
        self.get_quantity_list2(event)

    def confirm_agg_event(self):
        parent = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1',
        )
        entry_events = entries.EntryEvent.objects.filter(
            entry_id=parent.id, is_parent=True).values_list('event_id')
        evs = events.Event.objects.filter(id__in=entry_events)
        self.assertEqual(evs.count(), 2, 'There should only be two '
                                         'events that meet this criteria')
        event = events.Event.objects.get(
            id__in=entry_events,
            type=choices.EventTypeChoicesEnum.AGGREGATION.value)

        children = entries.EntryEvent.objects.filter(
            event_id=event.id, is_parent=False)
        self.assertEqual(children.count(), 5, 'There should be 5 children '
                                              'for the aggregation event.')

        logger.debug('Aggregation event item count checks out.')

        self.assertEqual(event.action, Action.add.value)
        self.assertEqual(event.type,
                         choices.EventTypeChoicesEnum.AGGREGATION.value)
        logger.debug('Agg event type is ok.')
        self.assertEqual(event.biz_step,
                         business_steps.BusinessSteps.packing.value)
        self.assertEqual(event.disposition,
                         dispositions.Disposition.container_closed.value)
        self.check_sglns(event)
        self.get_biz_transactions(event)
        self.get_quantity_list(event)
        self.get_source_destination(event)

    def check_sglns(self, event):
        self.assertEqual(event.read_point, 'urn:epc:id:sgln:305555.123456.12')
        self.assertEqual(event.biz_location, 'urn:epc:id:sgln:305555.123456.0')

    def get_biz_transactions(self, event, count=1):
        bizxact = events.BusinessTransaction.objects.filter(event_id=event.id)
        self.assertEqual(bizxact.count(), count,
                         'There should only be one biz '
                         'transaction for this event.')
        self.assertEqual(
            bizxact[0].type,
            business_transactions.BusinessTransactionType.Purchase_Order.value,
            'the business transaction type is not correct.')
        self.assertEqual(bizxact[0].biz_transaction,
                         'urn:epc:id:gdti:0614141.06012.1234')

    def confirm_transaction_event(self):
        parent = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1',
        )
        entry_events = entries.EntryEvent.objects.filter(
            entry_id=parent.id, is_parent=True).values_list('event_id')
        evs = events.Event.objects.filter(id__in=entry_events)
        self.assertEqual(evs.count(), 2, 'There should only be two '
                                         'events that meet this criteria')
        event = events.Event.objects.get(
            id__in=entry_events,
            type=choices.EventTypeChoicesEnum.TRANSACTION.value)
        self.check_sglns(event)
        self.get_biz_transactions(event)
        self.get_quantity_list(event)
        self.get_source_destination(event)
        self.assertEqual(event.action, Action.add.value)
        entry_event_ids = entries.EntryEvent.objects.filter(
            event_id=event.id,
            is_parent=False
        ).values_list('entry_id')
        self.assertEqual(entry_event_ids.count(), 5, 'There should only be'
                                                     'five event ids for the'
                                                     'children.')

    def get_quantity_list(self, event):
        qe1 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555555.*',
            quantity=5
        )
        self.assertIsNotNone(qe1, 'Could not locate one of'
                                  'the quantity elements.')
        qe2 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555555.*',
            quantity=14.5,
            uom='LB'
        )
        self.assertIsNotNone(qe2, 'Could not locate the LB quantity event.')

    def get_quantity_list2(self, event):
        qe1 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555551.*',
            quantity=100,
            uom='EA',
            is_output=False
        )
        self.assertIsNotNone(qe1, 'Could not locate one of'
                                  'the quantity elements.')
        qe2 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555551.*',
            quantity=94.3,
            uom='LB',
            is_output=False
        )
        self.assertIsNotNone(qe2, 'Could not locate the LB quantity event.')
        qe1 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555551.*',
            quantity=10,
            uom='EA',
            is_output=True
        )
        self.assertIsNotNone(qe1, 'Could not locate one of'
                                  'the quantity elements.')
        qe2 = events.QuantityElement.objects.get(
            event_id=event.id,
            epc_class='urn:epc:idpat:sgtin:305555.0555551.*',
            quantity=94.3,
            uom='LB',
            is_output=True
        )
        self.assertIsNotNone(qe2, 'Could not locate the LB quantity event.')


    def get_source_destination(self, event):
        sources = event.source_set.all()
        self.assertEqual(sources.count(), 2, 'There should only be two '
                                             'sources')
        source = sources.get(
            type='urn:epcglobal:cbv:sdt:possessing_party',
            source='urn:epc:id:sgln:305555.123456.0'
        )
        self.assertIsNotNone(source, 'the source '
                                     'urn:epc:id:sgln:305555.123456.0 '
                                     'was not found.')
        source = sources.get(
            type='urn:epcglobal:cbv:sdt:location',
            source='urn:epc:id:sgln:305555.123456.12'
        )
        self.assertIsNotNone(source, 'the source '
                                     'urn:epc:id:sgln:305555.123456.12'
                                     'was not found.')
        destinations = event.destination_set.all()
        self.assertEqual(destinations.count(), 2, 'There should only be '
                                                  'two destinations.')
        destinations.get(
            type='urn:epcglobal:cbv:sdt:owning_party',
            destination='urn:epc:id:sgln:309999.111111.0'
        )
        destinations.get(
            type='urn:epcglobal:cbv:sdt:location',
            destination='urn:epc:id:sgln:309999.111111.233'
        )

    def confirm_two_parents(self):
        entry = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1',
        )
        events = entries.EntryEvent.objects.filter(entry_id=entry.id)
        self.assertEqual(events.count(), 2)

    def confirm_business_step(self, event_id, business_step):
        pass

    def tearDown(self):
        pass
