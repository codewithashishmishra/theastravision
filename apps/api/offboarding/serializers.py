from rest_framework import serializers
from .models import Resignation, ClearanceItem


class ResignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resignation
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class ClearanceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearanceItem
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
