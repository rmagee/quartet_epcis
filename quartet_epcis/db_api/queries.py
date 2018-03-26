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

import logging
from EPCPyYes.core.v1_2 import template_events, events as pyyes_events
from quartet_epcis.models.choices import EventTypeChoicesEnum
from quartet_epcis.models import events, entries

logger = logging.getLogger(__name__)


def get_sources(db_event: events.Event):
    '''
    Returns each of the source events associated with the db_event
    parameter.

    :param: db_event: The event used to look up sources.
    :return: a QuerySet containing the source model instances associated
    with the db_event.
    '''
    source_events = events.SourceEvent.objects. \
        filter(event=db_event).values_list('source')
    return events.Source.objects.filter(id__in=source_events)


def get_destinations(db_event: events.Event):
    '''
    Returns each of the destination events associated with the db_event
    parameter.

    :param: db_event: The event used to look up destinations.
    :return: a QuerySet containing the destination model instances associated
    with the db_event.
    '''
    destination_events = events.DestinationEvent.objects. \
        filter(event=db_event).values_list('destination')
    return events.Destination.objects.filter(id__in=destination_events)


class EPCISDBProxy:
    '''
    Acts as a proxy between the abstracted database model and
    the EPCIS schema / XML model by converting queries for data into
    EPCPyYes objects.
    '''

    def get_epcis_event(self, db_event: events.Event):
        '''
        Takes the raw database event record and converts it to an EPCPyYes
        event.
        :param db_event: The database event instance.
        :return: An EPCPyYes template event of type Object,
        Transformation, Transaction or Aggregation.
        '''
        # look up the type
        if db_event.type == EventTypeChoicesEnum.OBJECT.value:
            ret = self._get_object_event(db_event)
        elif db_event.type == EventTypeChoicesEnum.AGGREGATION.value:
            ret = self._get_aggregation_event(db_event)
        elif db_event.type == EventTypeChoicesEnum.TRANSACTION.value:
            ret = self._get_transaction_event(db_event)
        else:
            ret = None
        # proxy out the call to the specific function
        return ret

    def get_error_declaration(self, db_event: events.Event,
                              p_event: pyyes_events.EPCISBusinessEvent):
        '''
        Creates a new ErrorDeclaration EPCPyYes instance and appends
        to p_event.
        :param db_event: The database model with the error declaration data.
        :param p_event: The the EPCPyYes business event to append the
        declaration to.
        '''
        # force eval of the queryset
        ed_list = list(db_event.errordeclaration_set.all())
        for ed in ed_list:
            error_declaration = pyyes_events.ErrorDeclaration()
            # get the event ids
            if ed.corrective_event_ids:
                error_declaration.corrective_event_ids = \
                    ed.corrective_event_ids.split(',')
            else:
                ed.corrective_event_ids = []
            # get the reason
            error_declaration.reason = ed.reason
            # get the declaration time and convert to iso string
            error_declaration.declaration_time = ed.declaration_time.isoformat()
            # append the ed to the epcpyyes event
            p_event.error_declaration = error_declaration

    def get_business_transactions(self, db_event: events.Event):
        '''
        Gets the business transaction info from an event and
        returns an EPCPyYes BusinessTransaction.
        :param db_event: The database event.
        :return: An EPCPyYes BusinessTransaction.
        '''
        bts = []
        bt_list = list(db_event.businesstransaction_set.all())
        for db_bt in bt_list:
            bt = pyyes_events.BusinessTransaction(db_bt.biz_transaction)
            bt.type = db_bt.type
            bts.append(bt)
        return bts

    def get_business_event(self, db_event: events.Event,
                           p_event: pyyes_events.EPCISBusinessEvent):
        '''
        Gets all the fields for a business event (the base
        event abstract model)
        :param db_event: The event
        :return:
        '''
        p_event.biz_location = db_event.biz_location
        p_event.read_point = db_event.read_point
        p_event.event_id = db_event.event_id
        p_event.disposition = db_event.disposition
        p_event.biz_step = db_event.biz_step
        p_event.action = db_event.action
        self.get_error_declaration(db_event, p_event)
        p_event.event_time = db_event.event_time.isoformat()
        p_event.event_timezone_offset = db_event.event_timezone_offset
        p_event.record_time = db_event.record_time.isoformat()
        p_event.business_transaction_list = self.get_business_transactions(
            db_event
        )
        p_event.source_list = self.get_source_list(db_event)
        p_event.destination_list = self.get_destination_list(db_event)
        return p_event

    def get_source_list(self, db_event: events.Event):
        '''
        Pulls each source out of the backend datastore and
        serializes to a list of EPCPyYes Source instances.
        :param db_event: The database Event model.
        :return: A list of EPCPyYes.core.v1_2.events.Source instances.
        '''
        ret = []
        se_list = events.SourceEvent.objects.select_related('source').filter(
            event=db_event
        )
        for se in se_list:
            source = pyyes_events.Source(
                source_type=se.source.type,
                source=se.source.source
            )
            ret.append(source)
        return ret

    def get_destination_list(self, db_event: events.Event):
        '''
        Pulls each destination out of the backend datastore and
        serializes to a list of EPCPyYes destination instances.
        :param db_event: The database Event model.
        :return: A list of EPCPyYes.core.v1_2.events.destination instances.
        '''
        ret = []
        dest_list = events.DestinationEvent.objects.select_related(
            'destination').filter(
            event=db_event
        )
        for dest in dest_list:
            destination = pyyes_events.Destination(
                destination_type=dest.destination.type,
                destination=dest.destination.destination
            )
            ret.append(destination)
        return ret

    def get_parent_epc(self, db_event: events.Event):
        '''
        For a given agg or transaction event, will get the parent epc.
        :param db_event: The event to retrieve the parent for.
        :return: A string representing the epc.
        '''
        try:
            ee = entries.EntryEvent.objects.select_related('entry').get(
                event=db_event,
                is_parent=True
            )
            return ee.entry.identifier
        except entries.EntryEvent.DoesNotExist:
            logger.info('No parent for event %s', db_event.id)

    def get_epc_list(self, db_event: events.Event, is_parent=False):
        '''
        Returns all of the EPCs for a given Event.
        :param db_event: The event to look up the EPCs (Entries) for.
        :return: A list of EPCs.
        '''
        ee = entries.EntryEvent.objects.select_related('entry').filter(
            event=db_event,
            is_parent=is_parent
        )
        return [e.entry.identifier for e in ee]

    def get_quantity_list(self, db_event: events.Event, is_output=False):
        '''
        Retrieves all of the Quantity data for a given Event.
        :param db_event: The Event go get the quantity data for.
        :return:
        '''
        qes = events.QuantityElement.objects.filter(
            event=db_event,
            is_output=is_output
        )
        return [
            pyyes_events.QuantityElement(
                qe.epc_class,
                quantity=qe.quantity,
                uom=qe.uom
            )
            for qe in qes
        ]

    def get_ilmd(self, db_event: events.Event):
        '''
        Gets all of the ILMD entries out of the backend relative to the
        db_event parameter and returns EPCPyYes ILMD class instances.
        :param db_event: The event to find ILMD data for.
        :return: A list of EPCPyYes ILMD class instances.
        '''
        ilmds = events.InstanceLotMasterData.objects.filter(event=db_event)
        return [
            pyyes_events.InstanceLotMasterDataAttribute(
                name=ilmd.name,
                value=ilmd.value
            )
            for ilmd in ilmds
        ]

    def _get_object_event(self, db_event: events.Event):
        '''
        Reconstructs a full object event based on the database
        model instance passed in.
        :param db_event: The object event event.Event instance.
        :return: An EPCPyYes template event ObjectEvent.
        '''
        o_event = template_events.ObjectEvent()
        self.get_business_event(db_event, o_event)
        o_event.epc_list = self.get_epc_list(db_event)
        o_event.quantity_list = self.get_quantity_list(db_event)
        o_event.ilmd = self.get_ilmd(db_event)
        return o_event

    def _get_aggregation_event(self, db_event: events.Event):
        '''
        Reconstructs a full aggregation event based on the database
        model instance passed in.
        :param db_event: The aggregation event event.Event instance.
        :return: An EPCPyYes template event AggregationEvent.
        '''
        agg_event = template_events.AggregationEvent()
        self.get_business_event(db_event, agg_event)
        agg_event.child_quantity_list = self.get_quantity_list(db_event)
        agg_event.child_epcs = self.get_epc_list(db_event)
        agg_event.parent_id = self.get_parent_epc(db_event)
        return agg_event

    def _get_transaction_event(self, db_event: events.Event):
        '''
        Reconstructs a full transaction event based on the database
        model instance passed in.
        :param db_event: The transaction event event.Event instance.
        :return: An EPCPyYes template event TransactionEvent.
        '''
        xact_event = template_events.TransactionEvent()
        self.get_business_event(db_event, xact_event)
        xact_event.epc_list = self.get_epc_list(db_event)
        xact_event.parent_id = self.get_parent_epc(db_event)
        xact_event.quantity_list = self.get_quantity_list(db_event)
        return xact_event

    def get_entries_by_event(self, db_event: events.Event):
        '''
        Get's all of the entries (serial numbers) for each event.
        :param db_event: The event to retrieve the numbers for.
        :return: A list of entry serial numbers/epcs.
        '''
        result = entries.EntryEvent.objects.prefetch_related.get(
            event=db_event)

    def get_events_by_entry_identifer(self, entry_identifier: str):
        '''
        Pulls all of the events out of the database based associated
        with the Entry.
        :param entry_identifier: The entry to use to lookup the event.
        :return: An models.Event instance.
        '''
        # get the entry_events
        ret = []
        events = list(
            entries.EntryEvent.objects.select_related('event').only(
                'event').filter(
                entry__identifier=entry_identifier
            ))
        for event in events:
            ret.append(event)
        return ret

    def _get_event_entries(self, db_event: events.Event):
        '''
        Returns all of the entries for a given event.
        :param db_event:
        :return: A list of entries.
        '''
        ret = []
        eevs = list(entries.EntryEvent.objects.select_related('entry').only(
            'event').filter(
            event=db_event))
        for eev in eevs:
            ret.append(eev.entry)
        return ret

    def _convert_event_to_pyyes(self, db_event: events.Event):
        '''
        Converts a database event into an EPCPyYes event.
        :param db_event: The database event
        :return: An EPCPyYes.core.v1_2 template event instance.
        '''
        # get the event's serial numbers
        entries = self._get_event_entries(db_event)
        # get the event's basic stuff
        if db_event.type == EventTypeChoicesEnum.OBJECT.value:
            event = self._get_object_event(db_event)
        elif db_event.type == EventTypeChoicesEnum.AGGREGATION.value:
            event = self._get_aggregation_event(db_event)
