# # This program is free software: you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with this program.  If not, see <http://www.gnu.org/licenses/>.
# #
# # Copyright 2018 SerialLab Corp.  All rights reserved.
#
# from quartet_epcis.app_models.EPCIS import events, entries, choices
# from EPCPyYes.core.v1_2 import template_events as yes_events
#
# def get_aggregation_event_by_id(
#     event_id: str
# )
#     '''
#     Returns an EPCPyYes object from the database based on the inbound
#     event id.
#     :param event_id: The event primary key.
#     :return: An EPCPyYes template_events.ObjectEvent
#     '''
#     db_event = events.Event.objects.get(id=event_id)
#     agg_event = yes_events.AggregationEvent
#     agg_event.event_id = db_event.event_id
#
# TODO: build out a nice query interface
