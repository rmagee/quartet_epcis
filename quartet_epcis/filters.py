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
import re
from gs123.conversion import BarcodeConverter
from quartet_masterdata.db import DBProxy
from gs123.regex import SGTIN_SN_10_13_ALPHA
from rest_framework.filters import SearchFilter
from logging import getLogger

logger = getLogger(__name__)

proxy = DBProxy()

class EntrySearchFilter(SearchFilter):
    """
    Will convert barcodes to URNS for search if one is detected.
    """

    def get_search_terms(self, request):
        terms = super().get_search_terms(request)
        transformed_terms = []
        for term in terms:
            match = SGTIN_SN_10_13_ALPHA.match(term)
            if match:
                try:
                    group_dict = match.groupdict()
                    cpl = proxy.get_company_prefix_length(group_dict['gtin14'])
                    transformed_terms.append(BarcodeConverter(company_prefix_length=cpl,
                                                              barcode_val=term).epc_urn)
                except:
                    logger.debug('Could not convert the barcode submitted %s',
                                 term)
                    transformed_terms.append(term)
            else:
                transformed_terms.append(term)
        return transformed_terms
