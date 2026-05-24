import uuid
from django.db import models
from organization.models import BaseTenantModel, Department
from employees.models import Employee


def interview_upload_path(instance, filename):
    tenant_id = getattr(instance, 'tenant_id', None) or 'unknown'
    return f'interviews/{tenant_id}/{filename}'


def resume_upload_path(instance, filename):
    tenant_id = getattr(instance, 'tenant_id', None) or 'unknown'
    return f'recruitment/resumes/{tenant_id}/{filename}'


def jd_upload_path(instance, filename):
    tenant_id = getattr(instance, 'tenant_id', None) or 'unknown'
    return f'recruitment/jd/{tenant_id}/{filename}'


class JobRequisition(BaseTenantModel):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Open', 'Open'),
        ('On Hold', 'On Hold'),
        ('Closed', 'Closed'),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Intern', 'Intern'),
    ]
    WORK_MODE_CHOICES = [
        ('On-site', 'On-site'),
        ('Hybrid', 'Hybrid'),
        ('Remote', 'Remote'),
    ]

    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    hiring_manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='job_reqs')
    headcount = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=100)
    description = models.TextField()
    jd_file = models.FileField(upload_to=jd_upload_path, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    target_hire_date = models.DateField(null=True, blank=True)
    match_threshold = models.PositiveIntegerField(default=70)
    assessment_enabled = models.BooleanField(default=False)
    auto_send_invite = models.BooleanField(default=False)
    voice_pass_threshold = models.PositiveIntegerField(default=60)
    interview_question_count = models.PositiveIntegerField(default=5)
    # Career board / job portal fields
    slug = models.SlugField(max_length=220, blank=True, default='')
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    employment_type = models.CharField(
        max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default='Full-time'
    )
    work_mode = models.CharField(max_length=50, choices=WORK_MODE_CHOICES, default='On-site')
    apply_deadline = models.DateField(null=True, blank=True)
    external_apply_url = models.URLField(max_length=500, null=True, blank=True)
    rich_description_html = models.TextField(blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'slug'],
                condition=~models.Q(slug=''),
                name='uniq_job_slug_per_tenant',
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class TenantCareerPortalSettings(models.Model):
    """Branding and API access for the public job board (Job Portal add-on)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'core.Tenant', on_delete=models.CASCADE, related_name='career_portal_settings'
    )
    slug = models.SlugField(max_length=100, unique=True)
    api_key_hash = models.CharField(max_length=128)
    api_key_prefix = models.CharField(max_length=16, help_text='Display prefix e.g. jb_live_ab12')
    allowed_embed_origins = models.JSONField(default=list, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, default='')
    primary_color = models.CharField(max_length=7, default='#2563eb')
    company_blurb = models.TextField(blank=True, default='')
    custom_domain = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Career portal: {self.slug}"


class Candidate(BaseTenantModel):
    STAGE_CHOICES = [
        ('Sourced', 'Sourced'),
        ('Screening', 'Screening'),
        ('Interview', 'Interview'),
        ('Offer', 'Offer'),
        ('Hired', 'Hired'),
        ('Rejected', 'Rejected'),
    ]

    job = models.ForeignKey(JobRequisition, on_delete=models.CASCADE, related_name='candidates')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    resume_url = models.URLField(max_length=500, null=True, blank=True)
    resume_file = models.FileField(upload_to=resume_upload_path, null=True, blank=True)
    parsed_resume_text = models.TextField(blank=True, default='')
    match_breakdown = models.JSONField(default=dict, blank=True)
    ai_match_score = models.IntegerField(default=0, help_text='AI calculated match score (0-100)')
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='Sourced')
    applied_on = models.DateTimeField(auto_now_add=True)
    proposed_reporting_manager = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='proposed_hires',
        help_text='Future reporting manager after hire',
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job.title}"


class Interview(BaseTenantModel):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    feedback_score = models.IntegerField(null=True, blank=True)
    feedback_notes = models.TextField(null=True, blank=True)
    magic_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    ai_session = models.ForeignKey(
        'AiInterviewSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='human_interviews'
    )

    def __str__(self):
        name = self.interviewer.first_name if self.interviewer else 'TBD'
        return f"Interview: {self.candidate.first_name} by {name}"


class AiInterviewSession(BaseTenantModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('voice_passed', 'Voice Passed'),
        ('assessment', 'Assessment'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ai_sessions')
    job = models.ForeignKey(JobRequisition, on_delete=models.CASCADE, related_name='ai_sessions')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    magic_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    consent_at = models.DateTimeField(null=True, blank=True)
    consent_ip = models.GenericIPAddressField(null=True, blank=True)
    current_question_index = models.PositiveIntegerField(default=0)
    overall_voice_score = models.FloatField(null=True, blank=True)
    assessment_score = models.FloatField(null=True, blank=True)
    proctor_flags = models.JSONField(default=dict, blank=True)
    invite_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"AI Session: {self.candidate} ({self.status})"


class AiInterviewQuestion(BaseTenantModel):
    session = models.ForeignKey(AiInterviewSession, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField()
    question_text = models.TextField()
    ideal_answer = models.TextField()
    rubric = models.TextField(blank=True, default='')
    candidate_transcript = models.TextField(blank=True, default='')
    audio_path = models.CharField(max_length=500, blank=True, default='')
    score_percent = models.FloatField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = [['session', 'order']]

    def __str__(self):
        return f"Q{self.order} for {self.session_id}"


class AssessmentTemplate(BaseTenantModel):
    job = models.OneToOneField(JobRequisition, on_delete=models.CASCADE, related_name='assessment_template')
    duration_minutes = models.PositiveIntegerField(default=20)
    question_count = models.PositiveIntegerField(default=10)
    proctor_interval_seconds = models.PositiveIntegerField(default=60)

    def __str__(self):
        return f"Assessment for {self.job.title}"


class AssessmentQuestion(BaseTenantModel):
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField()
    prompt = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    class Meta:
        ordering = ['order']
        unique_together = [['template', 'order']]


class AssessmentAttempt(BaseTenantModel):
    session = models.OneToOneField(AiInterviewSession, on_delete=models.CASCADE, related_name='assessment_attempt')
    answers = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    camera_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt for {self.session_id}"


class ProctorSnapshot(BaseTenantModel):
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='snapshots')
    captured_at = models.DateTimeField(auto_now_add=True)
    image_path = models.CharField(max_length=500)

    class Meta:
        ordering = ['-captured_at']


class AiInterviewReport(BaseTenantModel):
    session = models.OneToOneField(AiInterviewSession, on_delete=models.CASCADE, related_name='report')
    summary_html = models.TextField(blank=True, default='')
    summary_json = models.JSONField(default=dict, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Report for {self.session_id}"
