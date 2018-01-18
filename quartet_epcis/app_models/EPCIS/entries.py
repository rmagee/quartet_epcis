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
# Copyright 2018 SerialLab LLC.  All rights reserved.

from django.db import models
from django.utils.translation import gettext_lazy as _

from quartet_epcis.app_models.EPCIS import events, abstractmodels


class Entry(abstractmodels.UUIDModel):
    '''
    Represents an entry in the general ledger of serialized items and/or
    logical numbers used for serialized goods processing.
    '''
    id = models.CharField(
        max_length=150,
        null=False,
        help_text=_('The primary unique id for the entry.'),
        verbose_name=_('EPC URN'),
        db_index=True
    )
    events = models.ManyToManyField(events.Event)
    output = models.BooleanField(
        default=False,
        help_text=_('Whether or not this entry was the output of '
                    'a Transformation event.'),
        verbose_name=_('Transformation Output')
    )

    def __str__(self):
        return self.epc

    class Meta:
        verbose_name = _('Entry')
        verbose_name_plural = _('Entries')
