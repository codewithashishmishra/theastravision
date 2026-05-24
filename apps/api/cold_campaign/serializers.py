from rest_framework import serializers

from .copy_templates import default_campaign_copy
from .models import (
    ColdCampaign,
    ColdCampaignContentBatch,
    ColdCampaignContentVariant,
    ColdCampaignRecipient,
    ColdCampaignThreadMessage,
)


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
            'reply_status',
            'last_reply_at',
            'last_reply_snippet',
            'followup_step_sent',
            'next_followup_at',
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
            'is_paused',
            'followup_count',
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
            'generation_objective',
            'followup_count',
            'followup_delay_days',
            'followup_subject_template',
            'followup_body_html_template',
            'is_paused',
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
            'generation_objective',
            'followup_count',
            'followup_delay_days',
            'followup_subject_template',
            'followup_body_html_template',
        ]
        read_only_fields = ['id']

    def validate_followup_count(self, value):
        if value > 3:
            raise serializers.ValidationError('Maximum 3 follow-ups allowed.')
        return value

    def validate(self, attrs):
        count = attrs.get('followup_count')
        delays = attrs.get('followup_delay_days')
        if count is not None and delays is not None and count > 0:
            if len(delays) < count:
                raise serializers.ValidationError(
                    {'followup_delay_days': f'Provide {count} delay values (days).'}
                )
        return attrs

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
        if validated_data.get('followup_count', 0) > 0 and not validated_data.get('followup_delay_days'):
            count = validated_data['followup_count']
            validated_data['followup_delay_days'] = [3, 7, 14][:count]
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


class GenerateVariationsSerializer(serializers.Serializer):
    objective = serializers.ChoiceField(choices=ColdCampaign.OBJECTIVE_CHOICES)


class ApplyVariantSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()


class ColdCampaignContentVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColdCampaignContentVariant
        fields = ['id', 'variant_index', 'subject', 'body_html', 'body_text']
        read_only_fields = fields


class ColdCampaignContentBatchSerializer(serializers.ModelSerializer):
    variants = ColdCampaignContentVariantSerializer(many=True, read_only=True)

    class Meta:
        model = ColdCampaignContentBatch
        fields = ['id', 'campaign', 'objective', 'model', 'created_at', 'variants']
        read_only_fields = fields


class ContentLibraryVariantSerializer(serializers.ModelSerializer):
    batch_objective = serializers.CharField(source='batch.objective', read_only=True)
    batch_created_at = serializers.DateTimeField(source='batch.created_at', read_only=True)
    campaign_name = serializers.SerializerMethodField()

    class Meta:
        model = ColdCampaignContentVariant
        fields = [
            'id',
            'variant_index',
            'subject',
            'body_html',
            'body_text',
            'batch_objective',
            'batch_created_at',
            'campaign_name',
        ]

    def get_campaign_name(self, obj):
        if obj.batch.campaign_id:
            return obj.batch.campaign.name
        return None


class ColdCampaignThreadMessageSerializer(serializers.ModelSerializer):
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    campaign_id = serializers.UUIDField(source='recipient.campaign_id', read_only=True)
    campaign_name = serializers.CharField(source='recipient.campaign.name', read_only=True)

    class Meta:
        model = ColdCampaignThreadMessage
        fields = [
            'id',
            'recipient_email',
            'campaign_id',
            'campaign_name',
            'direction',
            'subject',
            'body_text',
            'received_at',
            'classification',
        ]
