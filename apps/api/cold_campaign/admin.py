from django.contrib import admin

from .models import ColdCampaign, ColdCampaignRecipient


class ColdCampaignRecipientInline(admin.TabularInline):
    model = ColdCampaignRecipient
    extra = 0
    readonly_fields = ('tracking_token', 'sent_at', 'opened_at', 'open_count')


@admin.register(ColdCampaign)
class ColdCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at', 'created_by')
    list_filter = ('status',)
    inlines = [ColdCampaignRecipientInline]


@admin.register(ColdCampaignRecipient)
class ColdCampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'campaign', 'status', 'opened_at', 'open_count')
    list_filter = ('status',)
