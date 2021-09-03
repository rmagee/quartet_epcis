from django.contrib import admin

from quartet_epcis.models import entries, events, headers
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from django.conf import settings


class NoCountPaginator(Paginator):
    @property
    def count(self):
        return 100 * 10  # Some arbitrarily large number,
        # so we can still get our page tab.


use_no_count = getattr(settings, 'OPTIMIZE_HIGH_COUNT_MODEL_ADMINS', True)


@admin.register(entries.Entry)
class EntryAdmin(admin.ModelAdmin):
    paginator = NoCountPaginator if use_no_count else Paginator
    show_full_result_count = False
    list_display = (
        'identifier',
        'last_disposition',
        'parent_id',
        'top_id',
        'last_event',
        'last_event_time',
        'created'
    )
    raw_id_fields = (
        'top_id',
        'parent_id',
        'last_event',
        'last_aggregation_event',
    )
    readonly_fields = (
        'last_event_time',
        'last_aggregation_event_time',
        'is_parent',
        'parent_id',
        'top_id',
        'last_event',
        'last_disposition',
        'last_aggregation_event'
    )
    search_fields = [
        'identifier'
    ]


@admin.register(entries.EntryEvent)
class EntryEventAdmin(admin.ModelAdmin):
    paginator = NoCountPaginator if use_no_count else Paginator
    show_full_result_count = False
    def url(self):
        return mark_safe(
            '<a class="download-task" href="%s%s">Download</a>' % (
                '/capture/task-data/', self.task_name))

    list_display = (
        'identifier',
        'event',
        'event_type',
        'task_name',
        url
    )
    search_fields = ['identifier']
    raw_id_fields = [
        'event',
        'entry'
    ]
    readonly_fields = (
        'event_type',
        'event_time',
        'entry',
        'event',
        'is_parent',
        'output',
        'event_time',
        'task_name'
    )


@admin.register(events.TransformationID)
class TransformationIDAdmin(admin.ModelAdmin):
    raw_id_fields = ('event',)


@admin.register(events.ErrorDeclaration)
class ErrorDeclarationAdmin(admin.ModelAdmin):
    pass


@admin.register(events.QuantityElement)
class QuantityElementAdmin(admin.ModelAdmin):
    raw_id_fields = ('event',)


@admin.register(events.BusinessTransaction)
class BusinessTransactionAdmin(admin.ModelAdmin):
    readonly_fields = ('event',)


class BusinessTransactionInline(admin.TabularInline):
    model = events.BusinessTransaction
    readonly_fields = ('event',)
    extra = 0


@admin.register(events.InstanceLotMasterData)
class InstanceLotMasterDataAdmin(admin.ModelAdmin):
    raw_id_fields = ('event',)


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


@admin.register(headers.SBDH)
class SBDHAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'document_identification',
    )
    readonly_fields = ('message',)


@admin.register(headers.Partner)
class PartnerAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'header',
    )


@admin.register(headers.DocumentIdentification)
class DocumentIdentificationAdmin(admin.ModelAdmin):
    pass


class ILMDInline(admin.TabularInline):
    model = events.InstanceLotMasterData
    raw_id_fields = ('event',)
    extra = 0


@admin.register(events.Event)
class EventAdmin(admin.ModelAdmin):
    paginator = NoCountPaginator if use_no_count else Paginator
    show_full_result_count = False
    list_display = (
        'action', 'biz_step', 'disposition', 'read_point', 'biz_location',
        'type', 'created'
    )
    inlines = [
        BusinessTransactionInline,
        ILMDInline
    ]
    search_fields = ['created']


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
    admin_site.register(headers.DocumentIdentification,
                        DocumentIdentificationAdmin)
    admin_site.register(headers.Partner, PartnerAdmin)
    admin_site.register(headers.SBDH, SBDHAdmin)
