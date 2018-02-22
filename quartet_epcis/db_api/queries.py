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


# TODO: build out a nice query interface
from quartet_epcis.models import events


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
