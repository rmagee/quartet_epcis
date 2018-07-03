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
import logging
from django.test import TestCase
from quartet_epcis.db_api.queries import EPCISDBProxy
from quartet_epcis.models import entries
from quartet_epcis.parsing.business_parser import BusinessEPCISParser

db_proxy = EPCISDBProxy()
logger = logging.getLogger(__name__)


class TestLargeFile(TestCase):
    '''
    Tests the EPCIS parser's business rule enforcement.
    '''

    def test_big_object_events(self):
        '''
        Commissions 15 or so thousand epcs.
        :return:
        '''
        self._parse_test_data(test_file='data/bigobject.xml')
        print(entries.Entry.objects.all().count())

    def _parse_test_data(self, test_file='data/epcis.xml',
                         parser_type=BusinessEPCISParser,
                         recursive_decommission=False):
        curpath = os.path.dirname(__file__)
        if isinstance(parser_type, BusinessEPCISParser):
            parser = parser_type(
                os.path.join(curpath, test_file),
                recursive_decommission=recursive_decommission
            )
        else:
            parser = parser_type(
                os.path.join(curpath, test_file),
            )
        message_id = parser.parse()
        return message_id, parser

    def _get_stream(self, file_name):
        curpath = os.path.dirname(__file__)
        return os.path.join(curpath, file_name)
