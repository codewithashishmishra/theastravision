from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from simple_history.models import HistoricalRecords
from functools import lru_cache

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email_domain = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Email domain for users in this tenant (e.g. aastraa.com)",
    )
    enabled_jurisdictions = models.JSONField(
        default=list,
        blank=True,
        help_text="Payroll jurisdictions enabled for this tenant: IN, US, CA",
    )
    
    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_plan = models.CharField(
        max_length=20, 
        choices=PLAN_CHOICES, 
        default='starter',
        help_text="Tenant's active subscription plan"
    )
    
    default_currency = models.CharField(max_length=3, default='INR')
    fiscal_year_start_month = models.IntegerField(default=4)
    variable_pay_enabled = models.BooleanField(
        default=False,
        help_text='Company-wide: allow variable pay component in salary structures',
    )
    allow_employee_variable_override = models.BooleanField(
        default=True,
        help_text='If true, per-employee variable_pay_enabled can override tenant default',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from core.jurisdictions import (
            default_currency_for_jurisdictions,
            fiscal_start_month_for_jurisdiction,
        )

        if not self.enabled_jurisdictions:
            self.enabled_jurisdictions = ['IN']
        self.default_currency = default_currency_for_jurisdictions(self.enabled_jurisdictions)
        self.fiscal_year_start_month = fiscal_start_month_for_jurisdiction(
            self.enabled_jurisdictions[0]
        )
        super().save(*args, **kwargs)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)
    
    # Advanced Auth Tracking
    is_email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Biometric Tracking
    face_encoding = models.JSONField(null=True, blank=True, help_text="128-dimensional face encoding vector")
    
    history = HistoricalRecords()

    def __str__(self):
        return self.username

class Permission(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True) # e.g. 'view_employee'
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)
    
    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return f"{self.name} ({self.tenant.name if self.tenant else 'Global'})"

class UserRoleMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_mappings')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_mappings')
    
    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class SystemAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at}] {self.user} - {self.action}"

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["module", "created_at"]),
        ]

# ----------------- ADVANCED AUTHENTICATION MODELS -----------------

class TOTPDevice(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class RecoveryCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=255)
    is_used = models.BooleanField(default=False)

class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    name = models.CharField(max_length=100) # e.g., "iPhone FaceID"

class MPINCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    mpin_hash = models.CharField(max_length=255)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

class TrustedDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_fingerprint = models.CharField(max_length=255, unique=True)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

class AuthSession(models.Model):
    LOGIN_METHODS = (
        ('password', 'Password'),
        ('totp', 'TOTP'),
        ('passkey', 'Passkey'),
        ('face_scan', 'Face Scan'),
    )
    CLIENT_TYPES = (
        ('web', 'Web Browser'),
        ('tracker', 'Desktop Tracker'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token_jti = models.UUIDField(unique=True)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, default='web')
    device_fingerprint = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    location_city = models.CharField(max_length=255, null=True, blank=True)
    location_country = models.CharField(max_length=255, null=True, blank=True)
    login_method = models.CharField(max_length=50, choices=LOGIN_METHODS, default='password')
    payload_key_wrapped = models.TextField(
        null=True,
        blank=True,
        help_text="AES-256 session data key wrapped with server master key (GCM)",
    )
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ConfigSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, default="default_env_key")
    wrapped_key = models.TextField(help_text="AES-GCM wrapped data key")
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_or_create_key(cls, name="default_env_key") -> bytes:
        from django.conf import settings as django_settings

        from core.gcm_crypto import generate_data_key, unwrap_data_key, wrap_data_key
        from cryptography.exceptions import InvalidTag

        try:
            settings_obj = cls.objects.get(name=name)
            try:
                return unwrap_data_key(settings_obj.wrapped_key)
            except InvalidTag:
                if not django_settings.DEBUG:
                    raise
                settings_obj.delete()
        except cls.DoesNotExist:
            pass

        data_key = generate_data_key()
        wrapped = wrap_data_key(data_key)
        cls.objects.update_or_create(name=name, defaults={"wrapped_key": wrapped})
        EnvConfiguration.get_cached_config.cache_clear()
        return data_key

class EnvConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.CharField(max_length=100, unique=True, help_text="Module name e.g., 'SMTP', 'DATABASE'")
    encrypted_config = models.TextField(help_text="AES-GCM encrypted JSON config mapped to base64")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_config(self, config_dict: dict):
        import json
        import base64
        from core.gcm_crypto import encrypt_blob
        
        data_key = ConfigSettings.get_or_create_key()
        json_str = json.dumps(config_dict)
        aad = f"env_config:{self.module}".encode('utf-8')
        encrypted_bytes = encrypt_blob(data_key, json_str.encode('utf-8'), aad)
        self.encrypted_config = base64.b64encode(encrypted_bytes).decode('ascii')
        
        # Clear LRU cache for this module
        EnvConfiguration.get_cached_config.cache_clear()
        
    def get_config(self) -> dict:
        import json
        import base64
        from core.gcm_crypto import decrypt_blob
        
        if not self.encrypted_config:
            return {}
            
        data_key = ConfigSettings.get_or_create_key()
        encrypted_bytes = base64.b64decode(self.encrypted_config)
        aad = f"env_config:{self.module}".encode('utf-8')
        try:
            decrypted_bytes = decrypt_blob(data_key, encrypted_bytes, aad)
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception:
            return {}

    @staticmethod
    @lru_cache(maxsize=128)
    def get_cached_config(module_name: str) -> dict:
        try:
            config = EnvConfiguration.objects.get(module=module_name)
            return config.get_config()
        except EnvConfiguration.DoesNotExist:
            return {}

class FeatureFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="e.g. ENABLE_NEW_UI")
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {'ON' if self.is_active else 'OFF'}"


class TenantAddon(models.Model):
    """Per-tenant product add-ons (enabled manually by Super Admin in v1)."""

    ADDON_JOB_PORTAL = 'job_portal'

    ADDON_CHOICES = [
        (ADDON_JOB_PORTAL, 'Job Portal & Career Board SDK'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='addons')
    addon_code = models.CharField(max_length=50, choices=ADDON_CHOICES)
    enabled = models.BooleanField(default=False)
    enabled_at = models.DateTimeField(null=True, blank=True)
    enabled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enabled_addons'
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'addon_code')

    def __str__(self):
        state = 'ON' if self.enabled else 'OFF'
        return f"{self.tenant.name} — {self.addon_code} ({state})"


class TenantEmailSettings(models.Model):
    """Per-tenant sender identity for outbound email (platform SMTP transport)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='email_settings')
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, default='AastraaHR')
    reply_to = models.EmailField(blank=True, default='')
    notify_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='Role names notified on email events, e.g. Company Admin, HR Admin',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.from_name} <{self.from_email}>'


class OutboundEmailLog(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    STATUS_OPENED = 'opened'

    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_OPENED, 'Opened'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='outbound_emails')
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True, default='')
    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=500)
    body_html = models.TextField(blank=True, default='')
    body_text = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    source = models.CharField(max_length=64, default='general')
    source_id = models.CharField(max_length=64, blank=True, default='')
    message_id = models.CharField(max_length=500, blank=True, default='')
    smtp_error = models.TextField(blank=True, default='')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails',
    )
    parent_log = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resends',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status', '-created_at']),
            models.Index(fields=['tenant', 'source']),
        ]

    def __str__(self):
        return f'{self.subject} → {self.to_emails}'
