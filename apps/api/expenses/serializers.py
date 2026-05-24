from rest_framework import serializers
from .models import ExpenseCategory, ExpensePolicy, ExpenseClaim


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class ExpensePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpensePolicy
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class ExpenseClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseClaim
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
