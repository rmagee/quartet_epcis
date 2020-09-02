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
# Copyright 2020 SerialLab Corp.  All rights reserved.
from EPCPyYes.core.v1_2 import events, events as yes_events
from quartet_epcis.parsing.business_parser import BusinessEPCISParser as bep
from quartet_capture.rules import RuleContext

class BusinessEPCISParser(bep):
    """
    Same core functionality as the BusinessEPCISParser from the business_parser
    module but can handle the quartet_capture RuleContext and use to store
    additional contextual values in the back end.
    """

    def __init__(self, stream, event_cache_size: int = 1024,
                 recursive_decommission: bool = True,
                 recursive_child_update: bool = False,
                 child_update_from_top: bool = True,
                 rule_context: RuleContext = None):
        super().__init__(stream, event_cache_size, recursive_decommission,
                         recursive_child_update, child_update_from_top)
        self.rule_context = rule_context
        self.counter = 0

    def clear_cache(self):
        """
        Sets the task name on Entry Events.
        :return: None
        """
        if self.rule_context:
            for entry_event in self.entry_event_cache:
                entry_event.task_name = self.rule_context.task_name
        super().clear_cache()


