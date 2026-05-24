from rest_framework import serializers
from .models import OnboardingChecklist, OnboardingTask, OnboardingAssignment, BGVRecord


class OnboardingChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingChecklist
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class OnboardingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTask
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class OnboardingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingAssignment
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class BGVRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BGVRecord
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
