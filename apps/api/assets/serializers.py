from rest_framework import serializers
from .models import Asset, AssetAssignment, AssetWarranty


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class AssetAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetAssignment
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class AssetWarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetWarranty
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
