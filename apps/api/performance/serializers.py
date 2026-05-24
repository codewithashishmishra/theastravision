from rest_framework import serializers
from .models import Goal, PerformanceReview


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class PerformanceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReview
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
