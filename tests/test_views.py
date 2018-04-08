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
import json
from quartet_epcis.parsing.parser import QuartetParser
from rest_framework.test import APITestCase
from django.urls import reverse
from quartet_epcis.models import events


class EPCISProxyViewTests(APITestCase):
    '''
    Tests each of the EPCISDBProxy view functions.
    '''

    def test_get_event_by_id(self):
        self._parse_test_data()
        db_event = events.Event.objects.all()[0]
        url = reverse('event-detail', args=[str(db_event.id)])
        result = self.client.get(url, format='json')
        content = json.loads(result.content.decode(result.charset))
        event = content['objectEvent']
        self.assertEqual(event['action'], 'ADD')
        self.assertEqual(event['eventTime'],
                         '2018-01-22T22:51:49.294565+00:00')
        self.assertEqual(event['bizStep'],
                         'urn:epcglobal:cbv:bizstep:commissioning')
        self.assertEqual(event['disposition'],
                         'urn:epcglobal:cbv:disp:encoded')
        self.assertEqual(event['readPoint'],
                         'urn:epc:id:sgln:305555.123456.12')
        self.assertEqual(event['bizLocation'],
                         'urn:epc:id:sgln:305555.123456.0')
        self.assertEqual(len(event['bizTransactionList']), 1)
        self.assertEqual(
            event['bizTransactionList']['urn:epc:id:gdti:0614141.06012.1234'],
            'urn:epcglobal:cbv:btt:po')
        self.assertEqual(len(event['sourceList']), 2)
        self.assertEqual(event['sourceList']['urn:epcglobal:cbv:sdt:location'],
                         'urn:epc:id:sgln:305555.123456.12')
        self.assertEqual(
            event['sourceList']['urn:epcglobal:cbv:sdt:possessing_party'],
            'urn:epc:id:sgln:305555.123456.0')
        self.assertEqual(len(event['destinationList']), 2)
        self.assertEqual(event['ilmd']['itemExpirationDate'], '2015-12-31')
        self.assertEqual(event['ilmd']['lotNumber'], 'DL232')
        # make sure the XML request works as well
        result = self.client.get(url, format='xml')
        print(result.content.decode(result.charset))


    def _parse_test_data(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        message_id = parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        return message_id
