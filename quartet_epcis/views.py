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
from typing import List
from gettext import gettext as _
from rest_framework import views
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from rest_framework import status
from EPCPyYes.core.v1_2 import template_events
from quartet_epcis.db_api.queries import EPCISDBProxy
from quartet_epcis.models import events

EventList = List[events.Event]
proxy = EPCISDBProxy()

class EventDetailView(views.APIView):
    def get(self, request: Request, format=None, event_id: str = None):
        '''
        Based on an inbound event id, will return the full event data as
        JSON or XML string.  The event_id that is passed in can be either the
        primary key of the event in the database or the actual EPCIS event_id
        value that uniquely identifies the event.

        The URI for a given event is as below (assuming that the urls.py
        was configured for access via `epcis`):

        .. code-block: text

            # default format is json so format query parameter is optional
            http[s]:/[hostname]:[port]/epcis/event-detail/[event id]/?format=[xml,json]

            # for example
            http://localhost:8000/epcis/event-detail/1d1fa10f-4421-4f2a-af10-4ddb4951807c/?format=json

        :return: A JSON string representing the event.
        '''

        response_data = {}
        try:
            if event_id:
                event = proxy.get_event_by_id(event_id)
                # render xml if the content type
                if 'xml' in request.content_type.lower() or \
                    'xml' in request.query_params.get('format', '') or \
                    format == 'xml':
                    response_data = event.render()
                else:
                    # else render JSON
                    response_data = event.render_dict()
            response = Response(response_data, status=status.HTTP_200_OK)
        except events.Event.DoesNotExist:
            response = Response('Event with id %s could not be '
                                'found' % event_id, status.HTTP_404_NOT_FOUND)
        return response


class EntryEventHistoryView(views.APIView):
    '''
    Returns all of the events associated with a given EPC/Entry.
    '''

    def get(self, request: Request, format=None, entry_pk: str = None,
            entry_identifier: str = None):
        '''
        Will pull out the event history of a given entry based on either
        it's primary key value in the data store or its identifier field
        which is typically the textual identifier such as an EPC urn.

        :param request: The HTTP request
        :param format: json or xml
        :param entry_pk: The entry primary key.
        :param entry_identifier: The entry identifier.
        :return: A series of XML or JSON structures representing the events
        associated with the inbound id.
        '''
        args = {'epc_pk': entry_pk} if entry_pk else {
            'epc': entry_identifier}
        # get a list of EPCPyYes events from the DB proxy
        events = proxy.get_events_by_epc(**args)
        if len(events) > 0:
            epcis_document = template_events.EPCISEventListDocument(events)
            if 'xml' in request.content_type.lower() or \
                'xml' in request.query_params.get('format', '') or \
                format == 'xml':
                    # render xml or...
                    response_data = epcis_document.render()
            else:
                # render json
                response_data = epcis_document.render_dict()
            return Response(response_data, status.HTTP_200_OK)
        else:
            raise NotFound(_('The entry with id %s could not be found.' % \
                             str(args)))


