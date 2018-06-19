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
from quartet_epcis.db_api.queries import EPCISDBProxy
from quartet_epcis.models import events, choices, headers, entries
from quartet_epcis.parsing import errors
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.parsing.business_parser import BusinessEPCISParser

db_proxy = EPCISDBProxy()


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
        '''
        Commissions, packs, ships and transforms.
        :return:
        '''
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
        '''
        Tries to pack an item that's already been packed.
        :return:
        '''
        self._parse_test_data()
        with self.assertRaises(errors.InvalidAggregationEventError):
            self._parse_test_data(test_file='data/bad_repack.xml')

    def test_recursive_decommission(self):
        '''
        Decommissions just the parent and the parser finds and decommissions
        the six child entries and then verifies.
        :return:
        '''
        # commission the items
        self._parse_test_data()
        # decommission the items
        self._parse_test_data('data/recursive_decommission.xml')
        # verify
        db_entries = entries.Entry.objects.filter(
            decommissioned=True
        )
        self.assertEqual(db_entries.count(), 6)

    def test_flat_decommission(self):
        '''
        Decommissions six entries and then verifies.
        :return:
        '''
        # commission the items
        self._parse_test_data()
        # decommission the items
        self._parse_test_data('data/decommission.xml',
                              recursive_decommission=False)
        # verify
        db_entries = entries.Entry.objects.filter(
            identifier__in=[
                'urn:epc:id:sgtin:305555.3555555.1',
                'urn:epc:id:sgtin:305555.0555555.1',
                'urn:epc:id:sgtin:305555.0555555.2',
                'urn:epc:id:sgtin:305555.0555555.3',
                'urn:epc:id:sgtin:305555.0555555.4',
                'urn:epc:id:sgtin:305555.0555555.5',
            ],
            decommissioned=True
        )
        self.assertEqual(db_entries.count(), 5)
        db_entries = db_proxy.get_entries_by_parent_identifier(
            'urn:epc:id:sgtin:305555.3555555.1',
            select_for_update=False
        )
        self.assertEqual(
            db_entries.count(),
            0,
            'There should be no child entries since'
            ' they have all been decommissioned.'
        )

    def test_nested_pack(self):
        '''
        Packs items to cases and cases to pallet and verifies.
        '''
        # commission the items first
        self._parse_test_data('data/commission.xml')
        # then pack
        self.assertEqual(
            entries.Entry.objects.all().count(),
            13
        )
        self._parse_test_data('data/nested_pack.xml')
        palet = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.5555555.1'
        )
        db_entries = db_proxy.get_entries_by_parent(palet)
        self.assertEqual(db_entries.count(), 2)
        for entry in db_entries:
            self.assertEqual(
                db_proxy.get_entries_by_parent(entry).count(),
                5
            )
        all_child = entries.Entry.objects.filter(
            top_id__identifier='urn:epc:id:sgtin:305555.5555555.1'
        )
        self.assertEqual(all_child.count(), 12)
        ee = entries.EntryEvent.objects.get(
            identifier='urn:epc:id:sgtin:305555.5555555.1',
            event_type=choices.EventTypeChoicesEnum.AGGREGATION.value,
            is_parent=True
        )
        self.assertIsNotNone(ee)
        evs = entries.EntryEvent.objects.filter(
            entry__in=entries.Entry.objects.all()
        )
        # 13 + 6 + 6 + 3 entry events should be stored.
        self.assertEqual(evs.count(), 28)
        self.assertEqual(all_child.count(), 12)

    def test_uncommissioned_pack(self):
        '''
        Tries to pack an item that hasn't been commissioned.
        '''
        with self.assertRaises(errors.EntryException):
            self._parse_test_data('data/nested_pack.xml')

    def test_unpack_top(self):
        '''
        Will unpack the top level (palet for example) and check
        that the children and children of children reflect the new top.
        This also tests an AGG event of DELETE that does not have a
        childEPCs list.
        '''
        # pack it all up
        self._parse_test_data('data/commission.xml')
        self._parse_test_data('data/nested_pack.xml')
        # unpack the top level
        self._parse_test_data('data/unpack_top.xml')
        # verify results
        # entries
        parent_entries = entries.Entry.objects.filter(
            identifier__in=[
                'urn:epc:id:sgtin:305555.3555555.1',
                'urn:epc:id:sgtin:305555.3555555.2'
            ],
            top_id=None
        )
        self.assertEqual(parent_entries.count(), 2)
        # make sure the top count is correct
        child_entries = entries.Entry.objects.filter(
            top_id__identifier__in=[
                'urn:epc:id:sgtin:305555.3555555.1',
                'urn:epc:id:sgtin:305555.3555555.2'
            ]
        )
        self.assertEqual(child_entries.count(), 10)
        # make sure the parent count is correct
        child_entries = entries.Entry.objects.filter(
            parent_id__identifier__in=[
                'urn:epc:id:sgtin:305555.3555555.1',
                'urn:epc:id:sgtin:305555.3555555.2'
            ]
        )
        self.assertEqual(child_entries.count(), 10)
        # make sure the old top now has no children
        old_entries = entries.Entry.objects.filter(
            top_id__identifier='urn:epc:id:sgtin:305555.5555555.1'
        )
        self.assertEqual(old_entries.count(), 0)
        evs = entries.EntryEvent.objects.filter(
            entry__in=entries.Entry.objects.all()
        )
        self.assertEqual(evs.count(), 29)

    def test_pack_top_in_new_top(self):
        '''
        Packs a top level into a new top level and checks to make sure
        the hierarchy is adjusted accordingly.
        '''
        # pack it all up
        self._parse_test_data('data/commission.xml')
        self._parse_test_data('data/nested_pack.xml')
        entry_count = entries.Entry.objects.filter(
            top_id__identifier='urn:epc:id:sgtin:305555.5555555.1'
        ).count()
        self.assertEqual(entry_count, 12)
        self._parse_test_data('data/top_in_new_top.xml')
        # verify
        entry_count = entries.Entry.objects.filter(
            top_id__identifier='urn:epc:id:sgtin:305555.5555555.2'
        ).count()
        self.assertEqual(entry_count, 13)

    def test_bad_parent(self):
        '''
        Tries to pack some valid entries into a parent id that was never
        commissioned.
        '''
        with self.assertRaises(errors.EntryException):
            self._parse_test_data('data/commission.xml')
            self._parse_test_data('data/bad_parent.xml')

    def test_pack_unpack_repack(self):
        '''
        Packs, unpacks and repacks an entry.
        '''
        self._parse_test_data('data/commission.xml')
        self.assertEqual(
            entries.Entry.objects.all().count(),
            13
        )
        self._parse_test_data('data/nested_pack.xml')
        palet = entries.Entry.objects.get(
            identifier='urn:epc:id:sgtin:305555.5555555.1'
        )
        db_entries = db_proxy.get_entries_by_parent(palet)
        self.assertEqual(db_entries.count(), 2)
        self._parse_test_data('data/unpack_item.xml')
        self._parse_test_data('data/repack_item.xml')

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
        print(parser.event_cache)
        parser.clear_cache()
        return message_id
