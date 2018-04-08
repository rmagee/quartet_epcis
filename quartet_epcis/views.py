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
import json
from rest_framework import views
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from quartet_epcis.db_api.queries import EPCISDBProxy
from quartet_epcis.models import events

proxy = EPCISDBProxy()

class EventDetailView(views.APIView):
    def get(self, request: Request, format=None, event_id: str=None):
        '''
        Based on an inbound event id, will return the full event data as
        JSON string.
        :return: A JSON string representing the event.
        '''
        response_data = {}
        try:
            if event_id:
                event = proxy.get_event_by_id(event_id)
                # render xml if the content type
                if 'xml' in request.content_type.lower() or \
                        'xml' in request.query_params.get('format', ''):
                    response_data = event.render(event.render())
                else:
                    # else render JSON
                    response_data = json.loads(event.render_json())
            response = Response(response_data, status=status.HTTP_200_OK)
        except events.Event.DoesNotExist:
            response = Response('Event with id %s could not be '
                                'found' % event_id, status.HTTP_404_NOT_FOUND)
        return response
