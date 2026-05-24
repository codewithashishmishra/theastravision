from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from assets.models import AssetAssignment
from core.tenant_utils import attach_tenant_to_request, get_employee_for_user

from .models import Employee, EmployeeBank, EmployeeContact, EmployeeWorkLocation
from .serializers_types import EmployeeWorkLocationSerializer
from .serializers_me import (
    EmployeeBankMeSerializer,
    EmployeeContactMeSerializer,
    EmployeeContactMeUpdateSerializer,
    EmployeeMeReadSerializer,
    MyAssetSerializer,
    UserMeSerializer,
)


def _user_payload(user):
    return UserMeSerializer(user).data


def _profile_flags(employee):
    if not employee:
        return {
            'has_employee': False,
            'has_bank': False,
            'has_assets': False,
        }
    has_bank = EmployeeBank.objects.filter(employee=employee).exists()
    has_assets = AssetAssignment.objects.filter(employee=employee).exists()
    return {
        'has_employee': True,
        'has_bank': has_bank,
        'has_assets': has_assets,
    }


class EmployeeMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attach_tenant_to_request(request)
        user = request.user
        employee = get_employee_for_user(user)
        if employee:
            employee = (
                Employee.objects.filter(pk=employee.pk)
                .select_related('department', 'designation', 'branch')
                .first()
            )

        payload = {
            'user': _user_payload(user),
            **_profile_flags(employee),
        }

        if employee:
            payload['employee'] = EmployeeMeReadSerializer(employee).data
            try:
                contact = employee.contact
            except EmployeeContact.DoesNotExist:
                contact = None
            payload['contact'] = (
                EmployeeContactMeSerializer(contact).data if contact else None
            )
        else:
            payload['employee'] = None
            payload['contact'] = None

        return Response(payload)

    def patch(self, request):
        attach_tenant_to_request(request)
        user = request.user
        employee = get_employee_for_user(user)

        user_fields = ('first_name', 'last_name', 'phone_number')
        user_updates = {k: request.data[k] for k in user_fields if k in request.data}
        if user_updates:
            for key, value in user_updates.items():
                setattr(user, key, value)
            user.save(update_fields=list(user_updates.keys()))

        contact_payload = request.data.get('contact')
        if contact_payload and employee:
            try:
                contact = employee.contact
            except EmployeeContact.DoesNotExist:
                contact = None

            if contact:
                ser = EmployeeContactMeUpdateSerializer(
                    contact, data=contact_payload, partial=True
                )
            else:
                ser = EmployeeContactMeUpdateSerializer(data=contact_payload)

            ser.is_valid(raise_exception=True)
            if contact:
                ser.save()
            else:
                ser.save(employee=employee, tenant_id=employee.tenant_id)

        return self.get(request)


class EmployeeMeBankView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attach_tenant_to_request(request)
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response(
                {'detail': 'No employee profile linked to this account.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            bank = employee.bank_details
        except EmployeeBank.DoesNotExist:
            return Response({'detail': 'not_found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(EmployeeBankMeSerializer(bank).data)


class EmployeeMeAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attach_tenant_to_request(request)
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response(
                {'detail': 'No employee profile linked to this account.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignments = (
            AssetAssignment.objects.filter(employee=employee)
            .select_related('asset')
            .order_by('-assigned_date')
        )
        return Response(MyAssetSerializer(assignments, many=True).data)


class EmployeeMeWorkLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attach_tenant_to_request(request)
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({'detail': 'No employee profile linked to this account.'}, status=404)
        obj, _ = EmployeeWorkLocation.objects.get_or_create(employee=employee, tenant_id=employee.tenant_id)
        return Response(EmployeeWorkLocationSerializer(obj).data)

    def patch(self, request):
        attach_tenant_to_request(request)
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({'detail': 'No employee profile linked to this account.'}, status=404)
        obj, _ = EmployeeWorkLocation.objects.get_or_create(employee=employee, tenant_id=employee.tenant_id)
        ser = EmployeeWorkLocationSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        if instance.has_home_coordinates() and instance.completed_at is None:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at', 'updated_at'])
        return Response(EmployeeWorkLocationSerializer(instance).data)
