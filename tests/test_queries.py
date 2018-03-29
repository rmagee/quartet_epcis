# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
import os
from django.test import TestCase
from quartet_epcis.models import events, choices, headers
from quartet_epcis.db_api import queries
from quartet_epcis.parsing.parser import QuartetParser


class QueriesTestCase(TestCase):
    '''
    This test case tests the db_api.EPCISDBProxy class, which acts
    as an abstraction layer between the flattend somewhat non-epcis
    back-end database and the developer.  The proxy class converts
    query results into `EPCPyYes.core.v1_2.template_event` (and SBDH)
    class instances which allow for clearer code and faster development.
    '''

    def test_get_message(self):
        '''
        Based on a Message model, get the full EPCIS document that
        represents that message as it was received as EPCPyYes objects.
        '''
        message_id = self._parse_test_data()
        message = headers.Message.objects.get(id=message_id)
        qp = queries.EPCISDBProxy()
        epcis_document = qp.get_full_message(message)
        self.assertEqual(len(epcis_document.transaction_events), 1)
        self.assertEqual(len(epcis_document.transformation_events), 1)
        self.assertEqual(len(epcis_document.object_events), 1)
        self.assertEqual(len(epcis_document.aggregation_events), 1)
        self.assertIsNotNone(epcis_document.header)
        print(epcis_document.render())

    def test_get_events(self):
        '''
        Pulls an object event out of the database.
        '''
        self._parse_test_data()
        qp = queries.EPCISDBProxy()
        evs = qp.get_events_by_entry_identifer(
            'urn:epc:id:sgtin:305555.0555555.1')
        self.assertEqual(3, len(evs))

    def test_get_object_event(self):
        self._parse_test_data()
        ae = events.Event.objects.filter(
            type=choices.EventTypeChoicesEnum.OBJECT.value
        )
        qp = queries.EPCISDBProxy()
        event = qp.get_epcis_event(ae[0])
        self.assertEqual(len(event.business_transaction_list), 1)
        self.assertEqual(len(event.source_list), 2)
        self.assertEqual(len(event.destination_list), 2)
        self.assertEqual(len(event.epc_list), 5)
        self.assertEqual(len(event.ilmd), 2)
        print(event.render())

    def test_get_header(self):
        '''
        Get the business document header.
        '''
        self._parse_test_data()
        ae = events.Event.objects.filter(
            type=choices.EventTypeChoicesEnum.OBJECT.value
        )
        qp = queries.EPCISDBProxy()
        header = qp.get_sbdh('55abd29c-010e-489e-af31-8f095b48dff9')
        self.assertEqual(len(header.partners), 2)
        print(header.render())

    def test_get_aggregation_event(self):
        self._parse_test_data()
        ae = events.Event.objects.filter(
            type=choices.EventTypeChoicesEnum.AGGREGATION.value
        )
        qp = queries.EPCISDBProxy()
        event = qp.get_epcis_event(ae[0])
        self.assertEqual(len(event.source_list), 2)
        self.assertEqual(len(event.destination_list), 2)
        self.assertEqual(len(event.child_epcs), 5)
        self.assertEqual(event.parent_id, 'urn:epc:id:sgtin:305555.3555555.1')
        print(event.render())

    def test_get_events_by_epc(self):
        self._parse_test_data()
        qp = queries.EPCISDBProxy()
        events = qp.get_events_by_epc('urn:epc:id:sgtin:305555.0555555.1')
        self.assertEqual(len(events), 3)

    def test_get_transaction_event(self):
        self._parse_test_data()
        te = events.Event.objects.filter(
            type=choices.EventTypeChoicesEnum.TRANSACTION.value
        )
        qp = queries.EPCISDBProxy()
        event = qp.get_epcis_event(te[0])
        self.assertEqual(len(event.business_transaction_list), 1)
        self.assertEqual(len(event.source_list), 2)
        self.assertEqual(len(event.destination_list), 2)
        self.assertEqual(len(event.epc_list), 5)
        self.assertEqual(event.parent_id, 'urn:epc:id:sgtin:305555.3555555.1')
        print(event.render())

    def test_get_transformation_event(self):
        self._parse_test_data()
        te = events.Event.objects.filter(
            type=choices.EventTypeChoicesEnum.TRANSFORMATION.value
        )
        qp = queries.EPCISDBProxy()
        event = qp.get_epcis_event(te[0])
        self.assertEqual(len(event.business_transaction_list), 2)
        self.assertEqual(len(event.source_list), 2)
        self.assertEqual(len(event.destination_list), 2)
        self.assertEqual(len(event.input_epc_list), 10)
        self.assertEqual(len(event.output_epc_list), 10)
        self.assertEqual(len(event.input_quantity_list), 2)
        self.assertEqual(len(event.output_quantity_list), 2)
        self.assertEqual(len(event.ilmd), 2)
        print(event.render())

    def _parse_test_data(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        message_id = parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        return message_id
