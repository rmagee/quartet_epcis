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
# Copyright 2018 SerialLab LLC.  All rights reserved.
import logging

from eparsecis.eparsecis import FastIterParser
from quartet_epcis.app_models.EPCIS import events
from quartet_epcis.app_models.EPCIS import entries
from EPCPyYes.core.v1_2 import events as yes_events

logger = logging.getLogger('quartet_epcis')


class QuartetParser(FastIterParser):
    def __init__(self, stream, event_cache_size: int = 1024,
                 entry_cache_size: int = 10240):
        '''
        Initializes a new QuartetParser.  Item entries and events will
        be cached in memory until either the event_cache_size or
        entry_cache_size limit is reached- whichever occurs first.

        Be aware that the size of the cached database entries may bump up
        against the size limits of query caches in certain RDBMS systems.

        :param stream: The EPCIS stream to parse.
        :param event_cache_size: defaults to 1024.  The number of events
        to cache in memory before pushing to the back-end datastore.
        :param entry_cache_size: The number of entries to cache before a
        push to the datastore occurs.
        '''
        super().__init__(stream)
        self.event_cache = []
        self.entry_cache = []
        self.quatity_element_cache = []
        self.error_declaration_cache = []
        self.cache_size = event_cache_size
        self.entry_cache_size = entry_cache_size

    def handle_transaction_event(
        self,
        epcis_event: yes_events.TransactionEvent
    ):
        '''
        Called whenever the parser has completed parsing a TransactionEvent
        within an EPCIS xml structure.

        :param epcis_event: An EPCPyYes TransactionEvent class instance.
        :return: None
        '''
        logger.debug('Handling a transaction event.')
        db_event = events.Event()
        db_event.action = epcis_event.action
        db_event.biz_location = epcis_event.biz_location or None
        db_event.biz_step = epcis_event.biz_step or None
        db_event.disposition = epcis_event.disposition or None
        db_event.read_point = epcis_event.read_point or None
        db_event.event_time = epcis_event.event_time
        db_event.event_timezone_offset = epcis_event.event_timezone_offset \
                                         or None
        db_event.event_id = epcis_event.event_id or None
        db_event.record_time = epcis_event.record_time or None
        self.handle_entries(db_event.id, epcis_event.epc_list)
        self.event_cache.append(db_event)

    def handle_entries(
        self, db_event_id: str, epc_list: [],
        output: bool = False
    ):
        '''
        Gets the EPCs from the event and caches them for strorage in the
        back-end.
        :param db_event_id: The unique id of the event
        :param epc_list: A list of epcs to be cached.
        :return:
        '''
        logging.debug('Processing epc list %s', epc_list)
        for epc in epc_list:
            entry = entries.Entry(identifier=epc, output=output)
            entry.events.add(db_event_id)
            self.entry_cache.append(entry)
            if len(self.entry_cache) >= self.entry_cache_size:
                self.clear_cache()

    def handle_error_declaration(
        self,
        db_event_id: str,
        error_declaration: yes_events.ErrorDeclaration,
    ):
        '''
        Creates an ErrorDeclaration database model and caches
        it for storage in the backend database.
        :param db_event_id: The unique id of the parent event.
        :param error_declaration: The EPCPyYes ErrorDeclaration instance.
        '''
        if isinstance(error_declaration.corrective_event_ids, list):
            logging.debug('Concatenating the corrective event ids')
            cids = ','.join(error_declaration.corrective_event_ids)
        else:
            cids = str(error_declaration.corrective_event_ids)
        ed = events.ErrorDeclaration(
            event_id=db_event_id,
            reason=error_declaration.reason,
            corrective_event_ids=cids,
        )
        self.error_declaration_cache.append(ed)

    def handle_quantity_element(
        self,
        db_event_id: str,
        quantity_element: yes_events.QuantityElement
    ):
        '''
        Creates a QuantityElement database model and caches it
        for later bulk insert into the backend database.
        :param db_event_id: The source event.
        :param quantity_element: The EPCPyYes QuantityElement
        '''
        qe = events.QuantityElement(
            event_id=db_event_id,
            epc_class=quantity_element.epc_class,
            quantity=quantity_element.quantity,
            uom=quantity_element.uom
        )
        self.quatity_element_cache.append(qe)

    def clear_cache(self):
        '''
        Calls save on all items in the cache
        '''
        logging.debug('Clear cache has been called with %s and %i '
                      'in the event and entry caches respectively',
                      len(self.event_cache), len(self.entry_cache))
        events.Event.objects.bulk_create(self.event_cache)
        entries.Entry.objects.bulk_create(self.entry_cache)
        logging.debug('Clearing cache of %s number of quantity elements',
                      len(self.quatity_element_cache))
        events.QuantityElement.objects.bulk_create(
            self.quatity_element_cache
        )
        logging.debug('Clearing cache of %s number of error declarations',
                      len(self.error_declaration_cache))
        events.ErrorDeclaration.objects.bulk_create(
            self.error_declaration_cache
        )

    def handle_object_event(self, epcis_event):
        pass

    def handle_aggregation_event(self, epcis_event):
        pass
