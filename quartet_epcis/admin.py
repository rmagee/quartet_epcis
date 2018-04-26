from django.contrib import admin

from quartet_epcis.models import entries, events, headers


@admin.register(entries.Entry, )
class EntryAdmin(admin.ModelAdmin):
    pass


@admin.register(entries.EntryEvent)
class EntryEventAdmin(admin.ModelAdmin):
    pass


@admin.register(events.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'action', 'biz_step', 'disposition', 'read_point', 'biz_location',
        'type'
    )


@admin.register(events.TransformationID)
class TransformationIDAdmin(admin.ModelAdmin):
    pass


@admin.register(events.ErrorDeclaration)
class ErrorDeclarationAdmin(admin.ModelAdmin):
    pass


@admin.register(events.QuantityElement)
class QuantityElementAdmin(admin.ModelAdmin):
    pass


@admin.register(events.BusinessTransaction)
class BusinessTransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(events.InstanceLotMasterData)
class InstanceLotMasterDataAdmin(admin.ModelAdmin):
    pass


@admin.register(events.Source)
class SourceAdmin(admin.ModelAdmin):
    pass


@admin.register(events.SourceEvent)
class SourceEventAdmin(admin.ModelAdmin):
    pass


@admin.register(events.Destination)
class DestinationAdmin(admin.ModelAdmin):
    pass


@admin.register(events.DestinationEvent)
class DestinationEventAdmin(admin.ModelAdmin):
    pass


@admin.register(headers.Message)
class MessageAdmin(admin.ModelAdmin):
    pass


@admin.register(headers.SBDH)
class SBDHAdmin(admin.ModelAdmin):
    pass


@admin.register(headers.Partner)
class PartnerAdmin(admin.ModelAdmin):
    pass


@admin.register(headers.DocumentIdentification)
class DocumentIdentificationAdmin(admin.ModelAdmin):
    pass


def register_to_site(admin_site):
    admin_site.register(entries.Entry, EntryAdmin)
    admin_site.register(entries.EntryEvent, EntryEventAdmin)
    admin_site.register(events.ErrorDeclaration, ErrorDeclarationAdmin)
    admin_site.register(events.Event, EventAdmin)
    admin_site.register(events.Destination, DestinationAdmin)
    admin_site.register(events.Source, SourceAdmin)
    admin_site.register(events.TransformationID, TransformationIDAdmin)
    admin_site.register(events.InstanceLotMasterData,
                        InstanceLotMasterDataAdmin)
    admin_site.register(events.BusinessTransaction, BusinessTransactionAdmin)
    admin_site.register(events.QuantityElement, QuantityElementAdmin)
    admin_site.register(headers.Message, MessageAdmin)
    admin_site.register(headers.DocumentIdentification, MessageAdmin)
    admin_site.register(headers.Partner, PartnerAdmin)
    admin_site.register(headers.SBDH, SBDHAdmin)
