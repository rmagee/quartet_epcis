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


from rest_framework.routers import DefaultRouter
from quartet_epcis import viewsets


router = DefaultRouter()
router.register(r'entries', viewsets.EntryViewSet, basename='entries')
router.register(r'entry-events', viewsets.EntryEventViewSet,
                basename='entry-events')
router.register(r'events', viewsets.EventViewSet, basename='events')
router.register(r'transformation-ids', viewsets.TransformationIDViewSet,
                basename='transformation-ids')
router.register(r'error-declarations', viewsets.ErrorDeclarationViewSet,
                basename='error-declarations')
router.register(r'quantity-elements', viewsets.QuantityElementViewSet,
                basename='quantity-elements')
router.register(r'business-transactions', viewsets.BusinessTransactionViewSet,
                basename='business-transactions')
router.register(r'ilmd', viewsets.InstanceLotMasterDataViewSet,
                basename='ilmd')
router.register(r'sources', viewsets.SourceViewSet, basename='sources')
router.register(r'source-events', viewsets.SourceEventViewSet,
                basename='source-events')
router.register(r'destinations', viewsets.DestinationViewSet,
                basename='destinations')
router.register(r'destination-event', viewsets.DestinationEventViewSet,
                basename='destinations')
router.register(r'messages',viewsets.MessageViewSet, basename='messages')
