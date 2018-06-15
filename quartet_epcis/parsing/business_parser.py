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
from django.utils.translation import gettext as _
from typing import List
from django.db.models import QuerySet
from quartet_epcis.db_api.queries import EPCISDBProxy
from quartet_epcis.parsing import errors
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.models import entries, choices, events as db_events
from EPCPyYes.core.v1_2 import events, events as yes_events

logger = logging.getLogger(__name__)

db_proxy = EPCISDBProxy()

EntryList = List[entries.Entry]


class BusinessEPCISParser(QuartetParser):

    def handle_aggregation_event(
        self,
        epcis_event: events.AggregationEvent
    ):
        '''
        Executed when an AggregationEvent xml structure has finished parsing.
        The rules by which AggregationEvents are handled in this module are
        spelled out in section 7.4.3 of the EPCIS 1.2 specification.

        :param epcis_event: An EPCPyYes AggregationEvent instance.
        '''
        logger.debug('Handling an aggregation event.')
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.AGGREGATION.value
        # see what kind of agg event we have here and process accordingly
        if epcis_event.action == events.Action.add.value:
            # TODO: check the date and update the parent if necessary
            # check the action date against the latest entry_event
            # if the event is after the last event then update the parent
            # data on the entry
            self._handle_aggregation_parent(db_event, epcis_event)
            self._handle_aggregation_entries(db_event, epcis_event)
        elif epcis_event.action == events.Action.delete.value:
            # TODO: check the data and remove the parent if necessary
            self._handle_delete_action(db_event, epcis_event)
        else:
            super().handle_aggregation_event(epcis_event)

    def handle_object_event(self, epcis_event: yes_events.ObjectEvent):
        db_event = self.get_db_event(epcis_event)
        db_event.type = choices.EventTypeChoicesEnum.OBJECT.value
        if epcis_event.action == events.Action.delete.value:
            db_entries = self._get_entries(epcis_event.epc_list)
            self._decommission_entries(db_entries, db_event, epcis_event)
        else:
            super().handle_object_event(epcis_event)

    def _handle_aggregation_entries(
        self, db_event: str, epcis_event: events.AggregationEvent
    ):
        '''
        Gets the EPCs from the event and caches them for storage in the
        back-end.  Then creates the EntryEvent intersection entity records
        and appends them for storage as well.
        :param db_event: The unique id of the event
        :param epc_list: A list of epcs to be cached.
        :return:
        '''
        if epcis_event.action == events.Action.add.value:
            # TODO: check the date and update the parent if necessary
            # check the action date against the latest entry_event
            # if the event is after the last event then update the parent
            # data on the entry
            event_time = epcis_event.event_time
            # get the entries and make sure none are decomissioned or
            # already packed inside another parent
            # step one- check the cache first!
            db_entries, count = self._get_entries_for_agggregation(
                epcis_event.child_epcs)
            # the count should be the same in the event and queryset
            if not count == len(epcis_event.child_epcs):
                raise errors.InvalidAggregationEventError(
                    'The aggregation event with id %s contained children '
                    'in the child_epc list that were either '
                    'never commissioned, decommissioned '
                    'or already in another aggregation.',
                    epcis_event.id
                )
            else:
                # ok, the count matches and they can be packed. now we
                # just check the parent to make sure that the parent is
                # a valid epc
                try:
                    parent = self._handle_aggregation_parent(
                        db_event,
                        epcis_event
                    )
                except entries.Entry.DoesNotExist:
                    raise errors.InvalidAggregationEventError(
                        'The parent epc %s was either never commissioned or'
                        'was decommissioned.'
                    )
                self._update_aggregation_entries(db_entries, parent, db_event,
                                                 epcis_event)
                for db_entry in db_entries:
                    entries.EntryEvent(
                        entry=db_entry,
                        event_time=epcis_event.event_time,
                        event=db_event,
                        event_type=db_event.type,
                        identifier=db_entry.identifier
                    )

        elif epcis_event.action == events.Action.delete.value:
            # TODO: check the data and remove the parent if necessary
            pass
        else:
            self.handle_entries(db_event, epcis_event.child_epcs,
                                epcis_event.event_time)

    def _get_entries_for_agggregation(self, epcs: list):
        '''
        Will pull entries first from the local entries cache then, if not
        found, will attempt to get them from the database.
        :param epcis_event: The event with the epcs to look for in the Entries
        cache and database model.
        :return: A two-tuple with a list or queryset of Entry model instances
        and an integer expressing the number of entries found.
        '''
        db_entries = []
        count = 0
        # try the local cache
        for epc in epcs:
            entry = self.entry_cache.get(epc)
            if entry and not entry.decommissioned and not entry.parent_id:
                db_entries.append(entry)
        count = len(db_entries)
        # if nothing was found, try the database
        if count == 0:
            kwargs = {'identifier__in': epcs,
                      'decommissioned': False,
                      'parent_id': None}
            db_entries = entries.Entry.objects.select_for_update().filter(
                **kwargs
            )
            count = db_entries.count()
        return db_entries, count

    def _update_aggregation_entries(
        self,
        db_entries,
        parent: entries.Entry,
        db_event: db_events.Event,
        epcis_event: events.AggregationEvent
    ):
        '''
        Will update the value of the entries and add them to the cache if they
        were not there already or just update the cache entries.  If a list
        is sent in then we assume the entries are already in the cache.
        If a queryset is sent in then we assume the entries are not in the
        cache and attempt to add them.
        :param entries: A queryset or list of entries.
        :return: None
        '''
        # the top is the parent's top or the parent itself...
        if isinstance(db_entries, list):
            for db_entry in db_entries:
                db_entry.last_aggregation_event_time = epcis_event.event_time
                db_entry.last_aggregation_event = db_event
                db_entry.last_aggregation_event_action = epcis_event.action
                db_entry.top_id = parent.top_id or parent
                db_entry.last_event = db_event
                db_entry.last_event_time = epcis_event.event_time
                db_entry.last_disposition = epcis_event.disposition
                db_entry.parent_id = parent
                db_entry.save()
        elif isinstance(db_entries, QuerySet):
            # update the database
            count = db_entries.update(
                parent_id=parent,
                top_id=parent.top_id or parent,
                last_aggregation_event=db_event,
                last_aggregation_event_time=epcis_event.event_time,
                last_aggregation_event_action=epcis_event.action,
                last_event=db_event,
                last_event_time=epcis_event.event_time,
                last_disposition=epcis_event.disposition
            )
            if count == 0:
                raise errors.EntryException('No Entry records were updated.')
            # then update the local cache if the db update was successful
            for entry in db_entries:
                self.entry_cache[entry.identifier] = entry

    def _update_event_entries(
        self,
        db_entries,
        db_event: db_events.Event,
        epcis_event: events.EPCISEvent
    ):
        '''
        Will update the value of the entries and add them to the cache if they
        were not there already or just update the cache entries.  If a list
        is sent in then we assume the entries are already in the cache.
        If a queryset is sent in then we assume the entries are not in the
        cache and attempt to add them.
        :param entries: A queryset or list of entries.
        :return: None
        '''
        # the top is the parent's top or the parent itself...
        if isinstance(db_entries, list):
            for db_entry in db_entries:
                db_entry.last_event = db_event
                db_entry.last_event_time = epcis_event.event_time
                db_entry.last_disposition = epcis_event.disposition
                db_entry.save()
        elif isinstance(db_entries, QuerySet):
            # update the database
            count = db_entries.update(
                last_event=db_event,
                last_event_time=epcis_event.event_time,
                last_disposition=epcis_event.disposition
            )
            if count == 0:
                raise errors.EntryException('No Entry records were updated.')
            # then update the local cache if the db update was successful
            for entry in db_entries:
                self.entry_cache[entry.identifier] = entry

    def _handle_aggregation_parent(self, db_event: db_events.Event,
                                   epcis_event: events.AggregationEvent):
        '''
        Will retrieve or create and store the parent and or/top level
        id as an Entry in the
        entry cache, create an EntryEvent and store that in the EntryEvent
        cache and return the new or existing Entry.

        :param top_id: The parent epc of an aggregation event.
        :param db_event: The Event model instance.
        :param epcis_event: The EPCPyYes event with the inbound event data.
        :return: An Entry model instance updated to reflect the current
        event being processed.
        '''
        # check the cache
        entry = self.entry_cache.get(
            epcis_event.parent_id,
            None,
        )
        if entry.decommissioned:
            raise errors.InvalidAggregationEventError(
                "The parent id %s for this event has been decommissioned.",
                epcis_event.parent_id
            )
        # not in the cache then get and put in the cache
        # since this is an agg event then the entry must already exist
        if not entry:
            try:
                entry = entries.Entry.objects.get(
                    identifier=epcis_event.parent_id,
                    decomissioned=False
                )
                self.entry_cache[entry.identifier] = entry
            except entries.Entry.DoesNotExist:
                raise errors.InvalidAggregationEventError(
                    "The parent id %s has not been commissioned and/or does"
                    "not exist in the database.  Therefor is invalid in the "
                    "context of an aggregation event."
                )
        # set all the pointers and convienince properties on the entry
        entry.last_aggregation_event_action = epcis_event.action
        entry.last_aggregation_event_time = epcis_event.event_time
        entry.last_aggregation_event = db_event
        entry.is_parent = True
        entry.last_event = db_event
        entry.last_event_time = epcis_event.event_time
        entry.last_disposition = epcis_event.disposition

        # create an entry event and add to the cache
        entryevent = entries.EntryEvent(entry=entry,
                                        event=db_event,
                                        event_time=db_event.event_time,
                                        event_type=db_event.type,
                                        identifier=epcis_event.parent_id,
                                        is_parent=True)
        self.entry_event_cache.append(entryevent)
        logger.debug('Cached Entry for top id %s', epcis_event.parent_id)
        return entry

    def _handle_children(self):
        pass
        # TODO if a parent has children and is being given a parent itself,
        # update the children with a new TOP

    def _handle_delete_action(self, db_event: db_events.Event,
                              epcis_event: events.AggregationEvent):
        pass
        # 1. see if there is a parent and children
        # if parent and children then set the parent and top of the children
        # to none

        # 2. if there is a parent and no children that means we remove all
        # children from the parent item per section 7.4.3 of the EPCIS 1.2
        # spec.

    def _get_entry(self, epc: str):
        '''
        Will look for an entry in the cache and then, if not found, from the
        database.  If it gets the entry from the database, it will then add
        it to the local cache.
        :param epc: The entry identifier to search for.
        :return: An Entry model instance.
        '''
        entry = self.entry_cache.get(epc)
        if not entry:
            entry = entries.Entry.objects.get(
                identifer=epc,
                decommissioned=False
            )
            # add it to the cache
            self.entry_cache[epc] = entry
        return entry

    def _screen_entries(self, entries: EntryList):
        '''
        Make sure that any entries that are not part of an EPCIS Agg,
        Transaction, Transformation or Object event if they have been
        decomissioned.
        :param entries:
        :return:
        '''
        for entry in EntryList:
            if entry.decommissioned:
                raise errors.DecommissionedEntryException(
                    _('The entry with identifier %s has been decommissioned'
                      ' and is not eligible to participate in subsequent '
                      'events after.', entry.identifier)
                )

    def _get_entries(self, epcs: list):
        '''
        Pulls first from the cache and then from the database.
        :param epcs: The epcs to use for lookup of entries.
        :return: A list or queryset of entries.
        '''
        db_entries = []
        for epc in epcs:
            epc = self.entry_cache.get(epc)
            if epc: db_entries.append(epc)
        if len(db_entries) != len(epcs):
            db_entries = db_proxy.get_entries_by_epcs(
                epcs,
                select_for_update=True
            )
            if db_entries.count() != len(epcs):
                raise errors.EntryException(
                    _('The number of entries returned does not match with '
                      'the number requested.')
                )
        return db_entries

    def _decommission_entries(
        self,
        db_entries: EntryList,
        db_event: db_events.Event,
        epcis_event: events.EPCISEvent
    ):
        '''
        Will mark each entry in the entry list as decommissioned.
        :param db_entries: The entries to set as decommissioned.
        :param recursive: Whether or not to decommission any child entries.
        Default = True
        '''
        if isinstance(db_entries, QuerySet):
            db_entries.update(
                decommissioned=True,
                last_event=db_event,
                last_event_time=epcis_event.event_time,
                last_disposition=epcis_event.disposition
            )
        else:
            for entry in db_entries:
                entry.decommissioned = True
                entry.last_event=db_event
                entry.last_event_time=epcis_event.event_time
                entry.last_disposition=epcis_event.disposition
                entry.save()
