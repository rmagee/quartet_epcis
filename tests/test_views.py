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
from quartet_epcis.models import events, entries
from quartet_epcis.management.commands.create_epcis_groups import \
    Command
from django.contrib.auth.models import User, Group

class EPCISProxyViewTests(APITestCase):
    '''
    Tests each of the EPCISDBProxy view functions.
    '''
    def setUp(self):
        user = User.objects.create_user(username='testuser',
                                        password='unittest',
                                        email='testuser@seriallab.local')
        Command().handle()
        oag = Group.objects.get(name='EPCIS Access')
        user.groups.add(oag)
        user.save()
        self.client.force_authenticate(user=user)
        self.user = user

    def test_get_event_by_id(self):
        self._parse_test_data()
        db_event = events.Event.objects.all()[0]
        url = reverse('event-detail', args=[str(db_event.id)])
        result = self.client.get(url, format='json')
        self.assertEqual(result.status_code, 200)
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

    def test_get_events_by_epc(self):
        self._parse_test_data()
        entry = entries.Entry.objects.all()[0]
        url = reverse('events-by-entry-id',
                      kwargs={'entry_identifier': entry.identifier})
        result = self.client.get(url, format='json')
        print(result.content.decode(result.charset))

    def test_get_events_by_ilmd(self):
        '''
        Ensures that the system can return lot information based on the
        ILMD data in the test database.
        '''
        self._parse_test_data()
        url = reverse('events-by-ilmd',
                      kwargs={'ilmd_name': 'lotNumber', 'ilmd_value': 'DL232'})
        result = self.client.get(url, format='json')
        print(result.content.decode(result.charset))
        self.assertEqual(result.status_code, 200)

    def _parse_test_data(self):
        curpath = os.path.dirname(__file__)
        parser = QuartetParser(
            os.path.join(curpath, 'data/epcis.xml')
        )
        message_id = parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        return message_id
