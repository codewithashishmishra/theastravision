"""Reporting hierarchy and org-tree API tests."""

from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Role, Tenant, User, UserRoleMapping
from employees.models import Employee, EmployeeType
from employees.services.employee_types import seed_employee_types_for_tenant


class OrgHierarchyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Org Test Co',
            domain='org-test',
            email_domain='orgtest.com',
        )
        seed_employee_types_for_tenant(self.tenant.id)
        self.emp_type = EmployeeType.objects.filter(tenant=self.tenant, code='OFFICE').first()

        self.hr_user = User.objects.create_user(
            username='hr@orgtest.com',
            email='hr@orgtest.com',
            password='password123',
            tenant=self.tenant,
        )
        role = Role.objects.create(tenant=self.tenant, name='HR Admin')
        UserRoleMapping.objects.create(user=self.hr_user, role=role)
        self.client.force_authenticate(user=self.hr_user)

    def _create_employee(self, code, first, last, manager=None):
        return Employee.objects.create(
            tenant=self.tenant,
            employee_code=code,
            first_name=first,
            last_name=last,
            date_of_joining=date.today(),
            employee_type=self.emp_type,
            status='Active',
            reporting_manager=manager,
        )

    def test_first_employee_without_manager_allowed(self):
        payload = {
            'employee_code': 'EMP-ROOT',
            'first_name': 'Alice',
            'last_name': 'Root',
            'date_of_joining': str(date.today()),
            'employee_type': str(self.emp_type.id),
            'status': 'Active',
        }
        response = self.client.post('/api/v1/employees/employees/', payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)

    def test_second_employee_without_manager_rejected(self):
        self._create_employee('EMP-ROOT', 'Alice', 'Root')
        payload = {
            'employee_code': 'EMP-002',
            'first_name': 'Bob',
            'last_name': 'Report',
            'date_of_joining': str(date.today()),
            'employee_type': str(self.emp_type.id),
            'status': 'Active',
        }
        response = self.client.post('/api/v1/employees/employees/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('reporting_manager', response.data)

    def test_cycle_detection(self):
        ceo = self._create_employee('EMP-CEO', 'Ceo', 'Boss')
        mgr = self._create_employee('EMP-MGR', 'Mid', 'Manager', manager=ceo)
        payload = {
            'reporting_manager': str(mgr.id),
        }
        response = self.client.patch(
            f'/api/v1/employees/employees/{ceo.id}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('reporting_manager', response.data)

    def test_org_tree_structure(self):
        ceo = self._create_employee('EMP-CEO', 'Ceo', 'Boss')
        mgr = self._create_employee('EMP-MGR', 'Mid', 'Manager', manager=ceo)
        self._create_employee('EMP-DEV', 'Dev', 'One', manager=mgr)

        response = self.client.get('/api/v1/employees/employees/org-tree/')
        self.assertEqual(response.status_code, 200)
        roots = response.data['roots']
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0]['name'], 'Ceo Boss')
        self.assertEqual(len(roots[0]['children']), 1)
        self.assertEqual(roots[0]['children'][0]['name'], 'Mid Manager')
        self.assertEqual(len(roots[0]['children'][0]['children']), 1)
        self.assertEqual(response.data['meta']['total'], 3)
