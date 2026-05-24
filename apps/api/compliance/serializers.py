from rest_framework import serializers

from .models import StatutoryRuleSet, ComplianceDocument, FilingRecord


class StatutoryRuleSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutoryRuleSet
        fields = '__all__'


class ComplianceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceDocument
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class FilingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilingRecord
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
