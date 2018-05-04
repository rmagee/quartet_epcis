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
from django.db.models import Q
from django.utils.translation import ugettext as _
from EPCPyYes.core.v1_2 import template_events, events as pyyes_events
from EPCPyYes.core.SBDH import sbdh, template_sbdh
from quartet_epcis.models.choices import EventTypeChoicesEnum
from quartet_epcis.models import events, entries, headers

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

    def get_full_message(self, message: headers.Message):
        '''
        Returns all of the events and hethe ader in a given message as
        a collection of EPCPyYes class instances.
        :param message: The message to use as the lookup for the header
        and event instances.
        :return: An EPCPyYes.core.v1_2.events.EPCISDocument with all parts
        associated with the given message.
        '''
        document = template_events.EPCISDocument()
        try:
            # first get the header if there was one
            db_header = headers.SBDH.objects.get(message=message)
            document.header = self._get_header(db_header)
        except SBDH.DoesNotExist:
            logger.debug('There was no document header associated '
                         'with message %s', message)
        # now get the events
        db_events = events.Event.objects.prefetch_related(
            'transformationid_set',
            'errordeclaration_set',
            'quantityelement_set',
            'businesstransaction_set',
            'instancelotmasterdata_set',
            'sourceevent_set__source',
            'destinationevent_set__destination',
        ).filter(message_id=message.id)
        pevents = [self.get_epcis_event(db_event) for db_event in
                   db_events]
        for event in pevents:
            if isinstance(event, pyyes_events.TransformationEvent):
                document.transformation_events.append(event)
            elif isinstance(event, pyyes_events.TransactionEvent):
                document.transaction_events.append(event)
            elif isinstance(event, pyyes_events.ObjectEvent):
                document.object_events.append(event)
            elif isinstance(event, pyyes_events.AggregationEvent):
                document.aggregation_events.append(event)
        return document

    def get_events_by_epc(self, epc: str = None, epc_pk: str = None):
        '''
        Returns a list of EPCPyEvents the epc was found in.
        :param epc: The epc to search events for.
        :param epc_pk: The primary key of the epc to search events for.
        :return: A list of EPCPyEvents
        '''
        args = {'identifier': epc} if epc else {'id': epc_pk}
        event_entries = entries.EntryEvent.objects.order_by(
            'event__event_time'
        ).select_related(
            'event'
        ).prefetch_related(
            'event__transformationid_set',
            'event__errordeclaration_set',
            'event__quantityelement_set',
            'event__businesstransaction_set',
            'event__instancelotmasterdata_set',
            'event__sourceevent_set__source',
            'event__destinationevent_set__destination',
        ).filter(**args)
        return [self.get_epcis_event(event_entry.event) for event_entry in
                event_entries]

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
        elif db_event.type == EventTypeChoicesEnum.TRANSFORMATION.value:
            ret = self._get_transformation_event(db_event)
        else:
            ret = None
        # proxy out the call to the specific function
        return ret

    def get_events_by_ilmd(self, name, value):
        '''
        Returns a list of EPCPyYes events by ILMD name value pair.
        Usefull for getting all events for a Lot, etc.
        :param name: The ILMD field name.
        :param value: The ILMD field value.
        :return: A list of EPCPyYes template_event instances.
        '''
        ilmds = events.InstanceLotMasterData.objects.select_related(
            'event'
        ).prefetch_related(
            'event__transformationid_set',
            'event__errordeclaration_set',
            'event__quantityelement_set',
            'event__businesstransaction_set',
            'event__instancelotmasterdata_set',
            'event__sourceevent_set__source',
            'event__destinationevent_set__destination',
        ).filter(
            name=name,
            value=value
        )
        return [self.get_epcis_event(ilmd.event) for ilmd in ilmds]

    def get_event_by_id(self, event_id: str):
        '''
        Looks up an event by it's primary key or event_id value.
        :param event_id: an event identifier that corresponds to one
        of the two values.
        :return: An Event model instance.
        '''
        db_event = events.Event.objects.get(
            Q(id=event_id) | Q(event_id=event_id))
        return self.get_epcis_event(db_event)

    def get_sbdh(self, instance_identifier: str):
        '''
        Use the instance identifier to retrieve a full EPCIS document
        standard business document header.
        :param instance_identifier: The unique id for the document.
        :return: A full EPCPyYes representation of the EPCIS message.
        '''
        try:
            db_header = headers.SBDH.objects.select_related(
                'document_identification',
                'message').prefetch_related('partner_set').get(
                document_identification__instance_identifier=
                instance_identifier)
            header = self._get_header(db_header)
            return header
        except headers.DocumentIdentification.DoesNotExist:
            raise headers.DocumentIdentification.DoesNotExist(
                _('The EPCIS document with instance identifier %s '
                  'could not be found in the database.' % instance_identifier)
            )

    def _get_header(self, db_header):
        '''
        Constucts an EPCPyYes header from the database header supplied.
        :param db_header:
        :return: An EPCPyYes header.
        '''
        if db_header.document_identification:
            # get the document identification data
            header = template_sbdh.StandardBusinessDocumentHeader()
            header.document_identification.instance_identifier = \
                db_header.document_identification.instance_identifier
            header.document_identification.creation_date_and_time = \
                db_header.document_identification.creation_date_and_time
            header.document_identification.standard = \
                db_header.document_identification.standard
            header.document_identification.type_version = \
                db_header.document_identification.type_version
            header.document_identification.multiple_type = \
                db_header.document_identification.multiple_type
            header.document_identification.document_type = \
                db_header.document_identification.document_type
        # get the partners
        header.partners = self.get_partner_list(db_header)
        return header

    def get_partner_list(self, db_header: headers.SBDH):
        '''
        Gets partner list information from the database and returns
        as EPCPyYes partner list.
        :param db_header: The database SBDH model instance.
        :return: A list of EPCPyYes.core.SBDH.sbdh.Partner instances
        '''
        ret = []
        for db_partner in db_header.partner_set.all():
            partner = sbdh.Partner(partner_type=sbdh.PartnerType(
                db_partner.partner_type))
            partner.partner_id = db_partner.identifier
            partner.contact_type_identifier = db_partner.contact_type_identifier
            partner.contact = db_partner.contact
            partner.telephone_number = db_partner.telephone_number
            partner.fax_number = db_partner.fax_number
            partner.email_address = db_partner.email_address
            ret.append(partner)
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
        logger.debug('Getting business event data for db event %s', db_event)
        p_event.biz_location = db_event.biz_location
        p_event.read_point = db_event.read_point
        p_event.disposition = db_event.disposition
        p_event.biz_step = db_event.biz_step
        p_event.action = db_event.action
        self.get_base_epcis_event(db_event, p_event)
        p_event.business_transaction_list = self.get_business_transactions(
            db_event
        )
        p_event.source_list = self.get_source_list(db_event)
        p_event.destination_list = self.get_destination_list(db_event)
        return p_event

    def get_base_epcis_event(self, db_event, p_event):
        '''
        All of the EPCPyYes events share a common base class.  This
        function pulls the data relative to the db_event out of the
        database and populates the base EPCPyYes EPCISEvent class
        fields.
        :param db_event: The database model class instance for the event.
        :param p_event: The EPCPyYes event that inherits from the
        base EPCISEvent class.
        '''
        logger.debug('Getting base epcis data for db event %s', db_event)
        self.get_error_declaration(db_event, p_event)
        p_event.event_time = db_event.event_time.isoformat()
        p_event.event_timezone_offset = db_event.event_timezone_offset
        p_event.record_time = db_event.record_time.isoformat()
        p_event.event_id = db_event.event_id

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

    def get_epc_list(
        self, db_event: events.Event, is_parent=False, output=False
    ):
        '''
        Returns all of the EPCs for a given Event.
        :param db_event: The event to look up the EPCs (Entries) for.
        :param is_parent: Whether or not to return any parent ids with
        the result.
        :param output: Whether or not to look for output epc values- only
        for use with transformation events.
        :return: A list of EPCs.
        '''
        ee = entries.EntryEvent.objects.select_related('entry').filter(
            event=db_event,
            is_parent=is_parent,
            output=output
        )
        return [e.entry.identifier for e in ee]

    def get_input_epc_list(self, db_event: events.Event):
        '''
        Just a helper function to make the code more clear when working
        with transformation events.
        :param xform_event: The transformation event to get the input epcs for.
        :return: A list of epc (string) values.
        '''
        return self.get_epc_list(db_event)

    def get_output_epc_list(self, db_event: events.Event):
        '''
        Just a helper function to make the code more clear when working
        with transformation events.
        :param xform_event: The transformation event to get the output
        epcs for.
        :return: A list of epc (string) values.
        '''
        return self.get_epc_list(db_event, output=True)

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

    def _get_transformation_event(self, db_event: events.Event):
        '''
        Reconstructs a full transformation event from the data
        in the database relative the the passed in db_event parameter.
        :param db_event: The event to use to pull the relevant data out
        of the database.
        :return: An EPCPyYes template_event TransformationEvent.
        '''
        xform_event = template_events.TransformationEvent()
        # get the basic EPCISEvent values
        self.get_base_epcis_event(db_event, xform_event)
        logger.debug('Hadling a transformation event %s', db_event)
        xform_event.input_epc_list = self.get_input_epc_list(db_event)
        xform_event.output_epc_list = self.get_output_epc_list(db_event)
        xform_event.input_quantity_list = self.get_quantity_list(db_event)
        xform_event.output_quantity_list = self.get_quantity_list(
            db_event, is_output=True
        )
        xform_event.destination_list = self.get_destination_list(db_event)
        xform_event.source_list = self.get_source_list(db_event)
        xform_event.ilmd = self.get_ilmd(db_event)
        xform_event.business_transaction_list = self.get_business_transactions(
            db_event
        )
        xform_event.biz_location = db_event.biz_location
        xform_event.read_point = db_event.read_point
        xform_event.disposition = db_event.disposition
        xform_event.biz_step = db_event.biz_step
        xform_event.transformation_id = self.get_transformation_id(db_event)
        return xform_event

    def get_transformation_id(self, db_event: events.Event):
        '''
        Looks up the transformation id for a given transformation event.
        :param db_event: The Event model instance to use for the lookup.
        :return: The transformation id as a string.
        '''
        try:
            tid = events.TransformationID.objects.get(event=db_event)
            return tid.identifier
        except events.TransformationID.DoesNotExist:
            logger.debug('No transformation id was found for event %s',
                         db_event)

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
