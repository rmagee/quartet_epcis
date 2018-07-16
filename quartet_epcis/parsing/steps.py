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

from quartet_capture import models
from quartet_capture.rules import Step as RuleStep
from quartet_capture.rules import RuleContext
from quartet_epcis.parsing.parser import QuartetParser
from quartet_epcis.parsing.business_parser import BusinessEPCISParser
from django.core.files.base import File
from quartet_capture.models import Rule, Step, StepParameter
from django.utils.translation import gettext as _


def create_rule(apps, schema_editor):
    '''
    Creates the default rule.  Used in data-migrations.
    :return: None
    '''
    rule = Rule.objects.create(
        name=_('EPCIS'),
        description=_('Will capture and parse all properly formed inbound '
                      'EPCIS messagess.  Loose or strict enforcement can '
                      'be controlled via step parameters.'),
    )
    step = Step.objects.create(
        name=_('Parse XML'),
        description=_('Parse EPCIS data and save to database. To set loose '
                      'enforcement (capture all messages) change the '
                      '"LooseEnforcement" step parameter to have a '
                      'value of True.'),
        step_class='quartet_epcis.parsing.steps.EPCISParsingStep',
        order=1,
        rule=rule
    )
    StepParameter.objects.create(
        step=step,
        name='LooseEnforcement',
        value='False',
        description=_('If set to true, QU4RTET will capture all properly '
                      'formed EPCIS messages regardless of business context.')
    )


class EPCISParsingStep(RuleStep):
    '''
    Calls the EPCIS parser as a rules.Step that can be used in the
    quartet_capture rule engine.
    '''

    def __init__(self, db_task: models.Task, **kwargs):
        super().__init__(db_task, **kwargs)
        # check to see which parser to use if loose enforcement, then
        # use the quartet parser which just captures messages without
        # trying to enforce any business rules (good for testing)
        loose_enforcement = self.parameters.get('LooseEnforcement', 'False')
        self.loose_enforcement = self.get_boolean_parameter(
            'LooseEnforcement', False)

    @property
    def declared_parameters(self):
        return {"LooseEnforcement": "Whether or not the parsing step should "
                                    "simply store the events (True) or if it "
                                    "should validate the EPCIS events using "
                                    "business rule processing. (False). "
                                    "Default is False"}

    def execute(self, data, rule_context: RuleContext):
        parser_type = QuartetParser if self.loose_enforcement else BusinessEPCISParser
        self.info('Loose Enforcement of busines rules set to %s',
                  self.loose_enforcement)
        self.info('Parsing message %s.dat', rule_context.task_name)
        try:
            if isinstance(data, File):
                parser = parser_type(data)
            else:
                parser = parser_type(io.BytesIO(data))
        except TypeError:
            parser = parser_type(io.BytesIO(data.encode()))
        parser.parse()
        self.info('Parsing complete.')

    def on_failure(self):
        pass
