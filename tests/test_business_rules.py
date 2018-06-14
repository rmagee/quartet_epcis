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
from django.test import TestCase, TransactionTestCase
from quartet_epcis.models import events, choices, headers, entries
from quartet_epcis.db_api import queries
from quartet_epcis.parsing import errors
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.parsing.business_parser import BusinessEPCISParser


class BusinessRulesTestCase(TestCase):
    '''
    Tests the EPCIS parser's business rule enforcement.
    '''

    def test_out_of_order_event(self):
        with self.assertRaises(QuartetParser.EventOrderException):
            self._parse_test_data(
                parser_type=QuartetParser,
                test_file='data/epcis-bad.xml'
            )

    def test_business_parsing(self):
        # parse the xml
        self._parse_test_data()
        # check the aggregation details
        parent_id = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.3555555.1')
        db_entries = entries.Entry.objects.filter(
            parent_id=parent_id
        )
        self.assertEqual(
            db_entries.count(), 5,
            "The entry count should have"
            "been 5 for parent %s" % \
            parent_id.identifier
        )

    def test_bad_repack(self):
        self._parse_test_data()
        with self.assertRaises(errors.InvalidAggregationEventError):
            self._parse_test_data(test_file='data/bad_repack.xml')

    def test_decommissioned_pack(self):
        pass

    def test_decommissioned_parent_id(self):
        pass

    def _parse_test_data(self, test_file='data/epcis.xml',
                         parser_type=BusinessEPCISParser):
        curpath = os.path.dirname(__file__)
        parser = parser_type(
            os.path.join(curpath, test_file)
        )
        message_id = parser.parse()
        print(parser.event_cache)
        parser.clear_cache()
        return message_id
