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
from typing import List
from eparsecis.eparsecis import EPCISParser
from quartet_epcis.app_models.EPCIS import events, choices, entries
from EPCPyYes.core.v1_2 import events as yes_events

logger = logging.getLogger('quartet_epcis')
biz_xact_list = List[yes_events.BusinessTransaction]
ilmd_list = List[yes_events.InstanceLotMasterDataAttribute]
source_list = List[yes_events.Source]
destination_list = List[yes_events.Destination]


class QuartetParser(EPCISParser):
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
        self.entry_cache = {}
        self.quantity_element_cache = []
        self.error_declaration_cache = []
        self.business_transaction_cache = []
        self.ilmd_cache = []
        self.source_cache = []
        self.destination_cache = []
        self.entry_event_cache = []
        self.event_cache_size = event_cache_size
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
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.TRANSACTION.value
        self.handle_entries(db_event.id, epcis_event.epc_list)
        if epcis_event.parent_id:
            self.handle_top_level_id(epcis_event.parent_id, db_event.id)
        self.handle_common_elements(db_event, epcis_event)
        self.event_cache.append(db_event)
        if len(self.event_cache) >= self.event_cache_size:
            self.clear_cache()

    def handle_top_level_id(self, top_id, db_event_id):
        '''
        For both transaction and aggregation events.  Will store the parent
        and or/top level id as an Entry in the entry cache.
        '''
        entry = self.entry_cache.get(top_id, entries.Entry(
            identifier=top_id))
        self.entry_cache[entry.identifier] = entry
        entryevent = entries.EntryEvent(entry_id=entry.id,
                                        event_id=db_event_id,
                                        identifier=top_id,
                                        is_parent=True)
        self.entry_event_cache.append(entryevent)
        logger.debug('Cached Entry for top id %s', top_id)

    def handle_aggregation_event(
        self,
        epcis_event: yes_events.AggregationEvent
    ):
        '''
        Executed when an AggregationEvent xml structure has finished parsing.

        :param epcis_event: An EPCPyYes AggregationEvent instance.
        '''
        logger.debug('Handling ann aggregation event.')
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.AGGREGATION.value
        self.handle_entries(db_event.id, epcis_event.child_epcs)
        self.handle_common_elements(db_event, epcis_event)
        self.handle_top_level_id(epcis_event.parent_id, db_event.id)
        self.event_cache.append(db_event)

    def handle_object_event(self, epcis_event: yes_events.ObjectEvent):
        '''
        Executed when an ObjectEvent xml structure has finished parsing.
        The EParseCIS library will pass in an EPCPyYes ObjectEvent
        class instance for use.

        :param epcis_event: The EPCPyYes ObjectEvent.
        '''
        logger.debug('Handling an ObjectEvent...')
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.OBJECT.value
        self.handle_entries(db_event.id, epcis_event.epc_list)
        self.handle_common_elements(db_event, epcis_event)
        self.handle_ilmd(db_event.id, epcis_event.ilmd)
        self.event_cache.append(db_event)

    def handle_transformation_event(
        self,
        epcis_event: yes_events.TransformationEvent
    ):
        '''
        Executed when a TransformationEvent xml element has completed parsing
        into a valid EPCPyYes TransformationEvent
        :param epcis_event: The EPCPyYes TransformationEvent
        :return: None
        '''
        logger.debug('Handling a TransformationEvent...')
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.TRANSFORMATION.value
        self.handle_common_elements(db_event, epcis_event)
        self.handle_entries(db_event.id, epcis_event.input_epc_list)
        self.handle_entries(db_event.id, epcis_event.output_epc_list,
                            output=True)
        self.handle_ilmd(db_event.id, epcis_event.ilmd)
        self.event_cache.append(db_event)

    def handle_common_elements(
        self,
        db_event: events.Event,
        epcis_event: yes_events.EPCISBusinessEvent
    ):
        '''
        Helper function to handle the common elements across the Object,
        Transaction and Aggregation event models.
        :param epcis_event: The Event django database model instance.
        :param db_event: The EPCPyYes EPCISBusinessEvent instance being passed
        to the parser.
        '''
        self.handle_business_transactions(
            db_event.id,
            epcis_event.business_transaction_list
        )
        self.handle_source_list(
            db_event.id,
            epcis_event.source_list
        )
        self.handle_destination_list(
            db_event.id,
            epcis_event.destination_list
        )
        if isinstance(epcis_event, yes_events.TransactionEvent) or \
            isinstance(epcis_event, yes_events.ObjectEvent):
            self.handle_quantity_elements(
                db_event.id,
                epcis_event.quantity_list
            )
        elif isinstance(epcis_event, yes_events.AggregationEvent):
            self.handle_quantity_elements(
                db_event.id,
                epcis_event.child_quantity_list
            )
        elif isinstance(epcis_event, yes_events.TransformationEvent):
            self.handle_quantity_elements(
                db_event.id,
                epcis_event.input_quantity_list
            )
            self.handle_quantity_elements(
                db_event.id,
                epcis_event.output_quantity_list,
                is_output=True
            )

    def get_db_event(self, epcis_event):
        '''
        Creates an Event database model with the common fields and returns.
        :param epcis_event: The EPCPyYes event.
        :return: A new Event model instance.
        '''
        db_event = events.Event()
        if not isinstance(epcis_event, yes_events.TransformationEvent):
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
        if epcis_event.error_declaration:
            self.handle_error_declaration(
                db_event.id,
                epcis_event.error_declaration
            )
        return db_event

    def handle_entries(
        self, db_event_id: str, epc_list: [],
        output: bool = False
    ):
        '''
        Gets the EPCs from the event and caches them for storage in the
        back-end.  Then creates the EntryEvent intersection entity records
        and appends them for storage as well.
        :param db_event_id: The unique id of the event
        :param epc_list: A list of epcs to be cached.
        :return:
        '''
        logging.debug('Processing epc list %s', epc_list)
        for epc in epc_list:
            entry = entries.Entry(identifier=epc)
            self.entry_cache[entry.identifier] = entry
            entryevent = entries.EntryEvent(entry_id=entry.id,
                                            event_id=db_event_id,
                                            identifier=epc,
                                            output=output)
            self.entry_event_cache.append(entryevent)
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

    def handle_quantity_elements(
        self,
        db_event_id: str,
        quantity_elements: list,
        is_output: bool = False,
    ):
        '''
        Creates a QuantityElement database model and caches it
        for later bulk insert into the backend database.
        :param db_event_id: The source event.
        :param quantity_element: The EPCPyYes QuantityElement
        '''
        for quantity_element in quantity_elements:
            qe = events.QuantityElement(
                event_id=db_event_id,
                epc_class=quantity_element.epc_class,
                quantity=quantity_element.quantity,
                uom=quantity_element.uom,
                is_output=is_output
            )
            logging.debug('Appending quantity element.')
            self.quantity_element_cache.append(qe)

    def handle_business_transactions(self, db_event_id: str,
                                     business_transaction_list: biz_xact_list):
        '''
        Takes each business transaction in the list and creates
        a BusinessTransaction database model instance and caches it
        for bulk insert into the backend database.
        :param db_event_id: The source event primary key/id.
        :param business_transaction_list: A list of EPCPyYes
        BusinessTransactions
        '''
        for transaction in business_transaction_list:
            bt = events.BusinessTransaction(
                event_id=db_event_id,
                biz_transaction=transaction.biz_transaction,
                type=transaction.type
            )
            logging.debug('Appending biz transaction.')
            self.business_transaction_cache.append(bt)

    def handle_ilmd(self, db_event_id: str,
                    ilmd_data: ilmd_list):
        '''
        Takes the ILMD node and creates InstanceLotMasterData model
        instances to be cached for bulk insert into the database.
        :param db_event_id: The source event primary key value.
        :param ilmd_data: The ilmd section of EPCPyYes event.
        '''
        for ilmd in ilmd_data:
            ie = events.InstanceLotMasterData(
                event_id=db_event_id,
                name=ilmd.name,
                value=ilmd.value,
            )
            self.ilmd_cache.append(ie)

    def handle_source_list(self, db_event_id: str,
                           sources: source_list):
        '''
        Creates a source database model instance and caches it
        for storage during bulk insert.
        :param db_event_id: The source event primary key.
        :param sources: A list of EPCPyYes Source instances.
        '''
        for source in sources:
            src = events.Source(
                type=source.type,
                source=source.source,
            )
            src.events.add(db_event_id)
            self.source_cache.append(src)

    def handle_destination_list(self, db_event_id: str,
                                destinations: destination_list):
        '''
        Creates a destination database model instance and caches
        it for storage during bulk insert.
        :param db_event_id: The source event's primary key.
        :param destinations: A list of EPCPyYes Destination instances.
        '''
        for destination in destinations:
            dest = events.Destination(
                type=destination.type,
                destination=destination.destination
            )
            dest.events.add(db_event_id)
            self.destination_cache.append(dest)

    def clear_cache(self):
        '''
        Calls save on all items in the cache
        '''
        logger.debug('Clear cache has been called with %s and %i '
                     'in the event and entry caches respectively',
                     len(self.event_cache), len(self.entry_cache))
        events.Event.objects.bulk_create(self.event_cache)
        entries.Entry.objects.bulk_create(self.entry_cache.values())
        logger.debug('Clearing out %s number of EntryEvents.',
                     len(self.entry_event_cache))
        entries.EntryEvent.objects.bulk_create(self.entry_event_cache)
        logger.debug('Clearing cache of %s number of quantity elements',
                     len(self.quantity_element_cache))
        events.QuantityElement.objects.bulk_create(
            self.quantity_element_cache
        )
        logger.debug('Clearing cache of %s number of error declarations',
                     len(self.error_declaration_cache))
        events.ErrorDeclaration.objects.bulk_create(
            self.error_declaration_cache
        )
        logger.debug('Clearing the biz transaction cache of %s transactions',
                     len(self.business_transaction_cache))
        events.BusinessTransaction.objects.bulk_create(
            self.business_transaction_cache
        )
        logger.debug('Clearing the ILMD cache of %s objects',
                     len(self.ilmd_cache))
        events.InstanceLotMasterData.objects.bulk_create(self.ilmd_cache)
        logger.debug('Clearing out the source cache of %s items',
                     len(self.source_cache))
        events.Source.objects.bulk_create(self.source_cache)
        logger.debug('Clearing out the destination cache of %s items',
                     len(self.destination_cache))
        events.Destination.objects.bulk_create(self.destination_cache)
        logger.debug('Clearing out the cache lists.')
        del self.event_cache[:]
        self.entry_cache.clear()
        del self.entry_event_cache[:]
        del self.error_declaration_cache[:]
        del self.quantity_element_cache[:]
        del self.business_transaction_cache[:]
        del self.ilmd_cache[:]
        del self.source_cache[:]
        del self.destination_cache[:]
