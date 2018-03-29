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

from django.db import models
from django.utils.translation import gettext_lazy as _

from quartet_epcis.models import abstractmodels


class Entry(abstractmodels.UUIDModel):
    '''
    Represents an entry in the general ledger of serialized items and/or
    logical numbers used for serialized goods processing.
    '''
    identifier = models.CharField(
        max_length=150,
        null=False,
        help_text=_('The primary unique id for the entry.'),
        verbose_name=_('EPC URN'),
        db_index=True,
        unique=True
    )

    def __str__(self):
        return self.identifier

    class Meta:
        verbose_name = _('Entry')
        verbose_name_plural = _('Entries')
        app_label = 'quartet_epcis'


class EntryEvent(models.Model):
    '''
    An intersection entity for events and entries.
    '''
    event = models.ForeignKey(
        'quartet_epcis.Event',
        null=False,
        help_text=_('The UUID of the event.'),
        verbose_name=_('Event ID'),
        db_index=True,
        on_delete=models.CASCADE
    )
    entry = models.ForeignKey(
        'quartet_epcis.Entry',
        null=False,
        help_text=_('The Unique ID of the Entry'),
        verbose_name=_('Entry ID'),
        db_index=True,
        on_delete=models.CASCADE
    )
    identifier = models.CharField(
        max_length=150,
        null=False,
        help_text=_('A redundant entry ID entry for fast event composition.'),
        verbose_name=_('EPC URN'),
    )
    is_parent = models.BooleanField(
        default=False,
        help_text=_('Whether or not this entry was the parent of it\'s '
                    'constituent event.'),
        verbose_name=_('Is Event Parent')
    )
    output = models.BooleanField(
        default=False,
        help_text=_('Whether or not the entry was the output of '
                    'a Transformation event.'),
        verbose_name=_('Transformation Output')
    )

    def __str__(self):
        return '{0}:{1}'.format(self.entry_id, event_id)

    class Meta:
        verbose_name = _('Entry Event Record')
        verbose_name_plural = _('Entry Event Records')
        index_together = ["event", "entry"]
        app_label = 'quartet_epcis'
