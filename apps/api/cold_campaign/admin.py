from django.contrib import admin

from .models import (
    ColdCampaign,
    ColdCampaignContentBatch,
    ColdCampaignContentVariant,
    ColdCampaignRecipient,
    ColdCampaignThreadMessage,
)


class ColdCampaignRecipientInline(admin.TabularInline):
    model = ColdCampaignRecipient
    extra = 0
    readonly_fields = ('tracking_token', 'sent_at', 'opened_at', 'open_count')


@admin.register(ColdCampaign)
class ColdCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'is_paused', 'followup_count', 'created_at', 'created_by')
    list_filter = ('status', 'is_paused')
    inlines = [ColdCampaignRecipientInline]


@admin.register(ColdCampaignRecipient)
class ColdCampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'campaign', 'status', 'reply_status', 'opened_at')
    list_filter = ('status', 'reply_status')


@admin.register(ColdCampaignContentBatch)
class ColdCampaignContentBatchAdmin(admin.ModelAdmin):
    list_display = ('objective', 'campaign', 'model', 'created_at')


@admin.register(ColdCampaignContentVariant)
class ColdCampaignContentVariantAdmin(admin.ModelAdmin):
    list_display = ('batch', 'variant_index', 'subject')


@admin.register(ColdCampaignThreadMessage)
class ColdCampaignThreadMessageAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'direction', 'classification', 'received_at')
