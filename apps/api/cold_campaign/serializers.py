from rest_framework import serializers

from .copy_templates import default_campaign_copy
from .models import ColdCampaign, ColdCampaignRecipient


class ColdCampaignRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColdCampaignRecipient
        fields = [
            'id',
            'email',
            'first_name',
            'company',
            'status',
            'sent_at',
            'opened_at',
            'open_count',
            'error_message',
            'created_at',
        ]
        read_only_fields = fields


class ColdCampaignListSerializer(serializers.ModelSerializer):
    total_recipients = serializers.IntegerField(read_only=True)
    sent_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    opened_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ColdCampaign
        fields = [
            'id',
            'name',
            'status',
            'subject',
            'from_name',
            'from_email',
            'total_recipients',
            'sent_count',
            'failed_count',
            'opened_count',
            'created_at',
            'updated_at',
        ]


class ColdCampaignDetailSerializer(serializers.ModelSerializer):
    total_recipients = serializers.IntegerField(read_only=True)
    sent_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    opened_count = serializers.IntegerField(read_only=True)
    recipients = ColdCampaignRecipientSerializer(many=True, read_only=True)

    class Meta:
        model = ColdCampaign
        fields = [
            'id',
            'name',
            'status',
            'subject',
            'body_html',
            'body_text',
            'from_name',
            'from_email',
            'trial_url',
            'total_recipients',
            'sent_count',
            'failed_count',
            'opened_count',
            'recipients',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'total_recipients',
            'sent_count',
            'failed_count',
            'opened_count',
            'recipients',
            'created_at',
            'updated_at',
        ]


class ColdCampaignWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColdCampaign
        fields = [
            'id',
            'name',
            'subject',
            'body_html',
            'body_text',
            'from_name',
            'from_email',
            'trial_url',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        trial_url = validated_data.get('trial_url') or ''
        defaults = default_campaign_copy(trial_url)
        if not validated_data.get('subject'):
            validated_data['subject'] = defaults['subject']
        if not validated_data.get('body_html'):
            validated_data['body_html'] = defaults['body_html']
        if not validated_data.get('body_text'):
            validated_data['body_text'] = defaults['body_text']
        campaign = ColdCampaign.objects.create(
            created_by=request.user if request and request.user.is_authenticated else None,
            **validated_data,
        )
        return campaign


class PreviewSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    company = serializers.CharField(required=False, allow_blank=True, default='')


class GenerateCopySerializer(serializers.Serializer):
    tone = serializers.CharField(required=False, default='professional')
