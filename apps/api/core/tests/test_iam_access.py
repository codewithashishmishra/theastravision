"""IAM API tenant isolation and access control tests."""

import uuid

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Role, Tenant, User, UserRoleMapping


class IamAccessControlTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant_a = Tenant.objects.create(name='Tenant A', domain='tenant-a', email_domain='a.com')
        self.tenant_b = Tenant.objects.create(name='Tenant B', domain='tenant-b', email_domain='b.com')

        self.admin_a = User.objects.create_user(
            username='admin@a.com',
            email='admin@a.com',
            password='password123',
            tenant=self.tenant_a,
        )
        role_a = Role.objects.create(tenant=self.tenant_a, name='IT Admin')
        UserRoleMapping.objects.create(user=self.admin_a, role=role_a)

        self.user_b = User.objects.create_user(
            username='user@b.com',
            email='user@b.com',
            password='password123',
            tenant=self.tenant_b,
        )
        role_b = Role.objects.create(tenant=self.tenant_b, name='Employee')
        UserRoleMapping.objects.create(user=self.user_b, role=role_b)

    def _login(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_users_list_denied(self):
        response = self.client.get('/api/v1/users/')
        self.assertIn(response.status_code, (401, 403))

    def test_tenant_admin_sees_only_own_users(self):
        self._login(self.admin_a)
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 200)
        emails = {row['email'] for row in response.data.get('results', response.data)}
        self.assertIn('admin@a.com', emails)
        self.assertNotIn('user@b.com', emails)

    def test_employee_cannot_list_users(self):
        self._login(self.user_b)
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 403)

    def test_tenant_list_requires_super_admin(self):
        self._login(self.admin_a)
        response = self.client.get('/api/v1/tenants/')
        self.assertEqual(response.status_code, 403)
