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
import io
from quartet_capture.rules import Step
from quartet_epcis.parsing.parser import QuartetParser
from django.core.files.base import File
from quartet_capture.models import Rule, Step

def create_rule(apps, schema_editor):
    '''
    Creates the default rule.  Used in data-migrations.
    :return: None
    '''
    rule = Rule.objects.create(
        name='EPCIS',
        description='Auto-Created EPCIS Parsing Rule.',
    )
    Step.objects.create(
        name='Parse XML',
        description='Parse EPCIS data and save to database.',
        step_class='quartet_epcis.parsing.steps.EPCISParsingStep',
        order=1,
        rule=rule
    )


class EPCISParsingStep(Step):
    '''
    Calls the EPCIS parser as a rules.Step that can be used in the
    quartet_capture rule engine.
    '''
    def declared_parameters(self):
        return {}

    def execute(self, data, rule_context: dict):
        try:
            if isinstance(data, File):
                parser = QuartetParser(data)
            else:
                parser = QuartetParser(io.BytesIO(data))
        except TypeError:
            parser = QuartetParser(io.BytesIO(data.encode()))
        parser.parse()
