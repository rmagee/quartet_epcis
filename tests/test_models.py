#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_quartet
------------

Tests for `quartet_epcis` models module.
"""
import os
import django
import logging

django.setup()
from django.test import TestCase
from EPCPyYes.core.v1_2.CBV import business_steps, business_transactions, \
    dispositions
from EPCPyYes.core.v1_2.events import Action
from quartet_capture import models
from quartet_capture.rules import RuleContext
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.parsing.business_parser import BusinessEPCISParser
from quartet_epcis.parsing.steps import EPCISParsingStep
from quartet_epcis.models import events, entries, choices
from quartet_epcis.db_api.queries import get_destinations, get_sources
logger = logging.getLogger(__name__)


class TestQuartet(TestCase):
    def setUp(self):
        pass

    def test_a_epcis_parser(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        self.run_parser(parser)
        parser = BusinessEPCISParser(
            os.path.join(curpath, 'data/epcis.xml')
        )

    def run_parser(self, parser):
        parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        self.confirm_parents()
        self.confirm_agg_event()
        self.confirm_transaction_event()
        self.confirm_object_event()
        self.confirm_transformation_event()

    def test_a_epcis_step(self):
        curpath = os.path.dirname(__file__)
        db_task = self._create_task()
        context = RuleContext(db_task.rule.name, task_name=db_task.name)
        step = EPCISParsingStep(db_task)
        with open(os.path.join(curpath, 'data/epcis.xml')) as f:
            step.execute(f.read(),context)
        self.confirm_parents()
        self.confirm_agg_event()
        self.confirm_transaction_event()
        self.confirm_object_event()
        self.confirm_transformation_event()

    def _create_task(self):
        db_task = models.Task()
        db_task.status = 'QUEUED'
        db_task.name = 'test'
        db_task.rule = self._create_rule()
        db_task.save()
        return db_task

    def _create_rule(self):
        db_rule = models.Rule()
        db_rule.name = 'epcis'
        db_rule.description = 'EPCIS Parsing rule utilizing quartet_epcis.'
        db_rule.save()
        rp = models.RuleParameter(name='test name', value='test value',
                                  rule=db_rule)
        rp.save()
        # create a new step
        epcis_step = models.Step()
        epcis_step.name = 'parse-epcis'
        epcis_step.description = 'Parse the EPCIS data and store in database.'
        epcis_step.order = 1
        epcis_step.step_class = 'quartet_epcis.parsing.steps.EPCISParsingStep'
        epcis_step.rule = db_rule
        epcis_step.save()
        return db_rule

    def confirm_parents(self):
        '''
        Makes sure there are two parent entries according
        to the input data
        '''
        res = entries.EntryEvent.objects.filter(is_parent=True)
        self.assertEqual(res.count(), 2, 'There should only be '
                                         'two parent entryevents.')
        for entry_event in res:
            logger.debug("Entry event __str__ check %s", str(entry_event))
        logger.debug('Parent count checks out.')
        self.confirm_three_parents()

    def confirm_object_event(self):
        item = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.0555555.1',
        )
        logger.debug('Entry __str__ check %s', item)
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
        self.assertEqual(serials.count(), 6,
                         'There should be six entry events'
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
        sources = get_sources(event)
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
        destinations = get_destinations(event)
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

    def confirm_three_parents(self):
        entry = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1',
        )
        events = entries.EntryEvent.objects.filter(entry_id=entry.id)
        # there is a third event for commissioning.
        self.assertEqual(events.count(), 3)

    def confirm_business_step(self, event_id, business_step):
        pass

    def tearDown(self):
        pass
