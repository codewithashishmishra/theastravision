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


def bug_report_upload_path(instance, filename):
    tenant_id = getattr(instance, 'tenant_id', None) or 'unknown'
    session_id = getattr(instance, 'session_id', None) or 'unknown'
    return f'interviews/{tenant_id}/{session_id}/bug-reports/{filename}'


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
    PARSE_PENDING = 'pending'
    PARSE_PROCESSING = 'processing'
    PARSE_READY = 'ready'
    PARSE_FAILED = 'failed'
    PARSE_STATUS_CHOICES = [
        (PARSE_PENDING, 'Pending'),
        (PARSE_PROCESSING, 'Processing'),
        (PARSE_READY, 'Ready'),
        (PARSE_FAILED, 'Failed'),
    ]
    jd_parse_status = models.CharField(
        max_length=16, choices=PARSE_STATUS_CHOICES, default=PARSE_READY
    )
    jd_parse_error = models.CharField(max_length=500, blank=True, default='')

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


class RecruitmentCampaign(BaseTenantModel):
    STATUS_DRAFT = 'draft'
    STATUS_SENDING = 'sending'
    STATUS_SENT = 'sent'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENDING, 'Sending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PAUSED, 'Paused'),
    ]

    title = models.CharField(max_length=200)
    job = models.OneToOneField(
        JobRequisition, on_delete=models.CASCADE, related_name='recruitment_campaign'
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    outreach_subject = models.CharField(max_length=500, blank=True, default='')
    outreach_body_html = models.TextField(blank=True, default='')
    outreach_body_text = models.TextField(blank=True, default='')
    send_rate_per_minute = models.PositiveIntegerField(default=10)
    default_reporting_manager = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='recruitment_campaigns',
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruitment_campaigns_created',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.status})'


class RecruitmentCampaignAttachment(BaseTenantModel):
    KIND_JD_EXTRACT = 'jd_extract'
    KIND_CHOICES = [
        (KIND_JD_EXTRACT, 'JD Extract'),
    ]

    campaign = models.ForeignKey(
        RecruitmentCampaign, on_delete=models.CASCADE, related_name='attachments'
    )
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default=KIND_JD_EXTRACT)
    file_path = models.CharField(max_length=500, blank=True, default='')
    extracted_text = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['campaign', 'kind'])]

    def __str__(self):
        return f'Attachment {self.kind} for {self.campaign_id}'


class RecruitmentCampaignQuestion(BaseTenantModel):
    SOURCE_JD_BASELINE = 'jd_baseline'
    SOURCE_CHOICES = [
        (SOURCE_JD_BASELINE, 'JD Baseline'),
    ]

    campaign = models.ForeignKey(
        RecruitmentCampaign, on_delete=models.CASCADE, related_name='campaign_questions'
    )
    order = models.PositiveIntegerField()
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_JD_BASELINE)
    difficulty_tier = models.CharField(max_length=32, blank=True, default='')
    question_text = models.TextField()
    ideal_answer = models.TextField()

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['campaign', 'order', 'source'],
                name='uniq_campaign_question_source_order',
            )
        ]
        indexes = [models.Index(fields=['campaign', 'source', 'order'])]

    def __str__(self):
        return f'CampaignQ {self.order} for {self.campaign_id}'


class Candidate(BaseTenantModel):
    OUTREACH_PENDING = 'pending'
    OUTREACH_SENT = 'sent'
    OUTREACH_OPENED = 'opened'
    OUTREACH_RESUME_UPLOADED = 'resume_uploaded'
    OUTREACH_MATCHED = 'matched'
    OUTREACH_COMPLETED = 'completed'
    OUTREACH_STATUS_CHOICES = [
        (OUTREACH_PENDING, 'Pending'),
        (OUTREACH_SENT, 'Sent'),
        (OUTREACH_OPENED, 'Opened'),
        (OUTREACH_RESUME_UPLOADED, 'Resume uploaded'),
        (OUTREACH_MATCHED, 'Matched'),
        (OUTREACH_COMPLETED, 'Completed'),
    ]

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
    campaign = models.ForeignKey(
        RecruitmentCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
    )
    portal_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    outreach_status = models.CharField(
        max_length=32, choices=OUTREACH_STATUS_CHOICES, default=OUTREACH_PENDING
    )
    outreach_sent_at = models.DateTimeField(null=True, blank=True)
    resume_parse_status = models.CharField(
        max_length=16,
        choices=JobRequisition.PARSE_STATUS_CHOICES,
        default=JobRequisition.PARSE_READY,
    )
    resume_parse_error = models.CharField(max_length=500, blank=True, default='')

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
    include_assessment = models.BooleanField(
        default=False,
        help_text='HR opted in at invite time; assessment is not sent unless this is true.',
    )
    session_recording_path = models.CharField(max_length=500, blank=True, default='')
    camera_recording_path = models.CharField(max_length=500, blank=True, default='')
    recording_started_at = models.DateTimeField(null=True, blank=True)
    recording_ended_at = models.DateTimeField(null=True, blank=True)
    candidate_feedback = models.JSONField(default=dict, blank=True)

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
    skipped = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = [['session', 'order']]

    def __str__(self):
        return f"Q{self.order} for {self.session_id}"


class CandidatePrebakedQuestion(BaseTenantModel):
    TIER_LOW = 'low'
    TIER_MEDIUM = 'medium'
    TIER_HARD = 'hard'
    TIER_EXTREME_HARD = 'extreme_hard'
    TIER_CHOICES = [
        (TIER_LOW, 'Low'),
        (TIER_MEDIUM, 'Medium'),
        (TIER_HARD, 'Hard'),
        (TIER_EXTREME_HARD, 'Extreme Hard'),
    ]

    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='prebaked_questions'
    )
    session = models.ForeignKey(
        AiInterviewSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prebaked_questions',
    )
    campaign = models.ForeignKey(
        RecruitmentCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidate_prebaked_questions',
    )
    order = models.PositiveIntegerField()
    difficulty_tier = models.CharField(max_length=32, choices=TIER_CHOICES)
    question_text = models.TextField()
    ideal_benchmarked_response = models.TextField()

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'session', 'order'],
                name='uniq_candidate_session_prebaked_order',
            )
        ]
        indexes = [
            models.Index(fields=['session', 'order']),
            models.Index(fields=['candidate', 'created_at']),
        ]

    def __str__(self):
        return f'Prebaked Q{self.order} for {self.candidate_id}'


class CandidateLiveResponse(BaseTenantModel):
    STATUS_ANSWERED = 'answered'
    STATUS_SKIPPED = 'skipped'
    STATUS_REPEATED = 'repeated'
    STATUS_TIMEOUT = 'timeout'
    STATUS_CHOICES = [
        (STATUS_ANSWERED, 'Answered'),
        (STATUS_SKIPPED, 'Skipped'),
        (STATUS_REPEATED, 'Repeated'),
        (STATUS_TIMEOUT, 'Timeout'),
    ]

    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name='live_responses'
    )
    session = models.ForeignKey(
        AiInterviewSession, on_delete=models.CASCADE, related_name='live_responses'
    )
    interview_question = models.ForeignKey(
        AiInterviewQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='live_responses',
    )
    prebaked_question = models.ForeignKey(
        CandidatePrebakedQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='live_responses',
    )
    question_order = models.PositiveIntegerField()
    transcript_text = models.TextField(blank=True, default='')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ANSWERED)
    silence_seconds = models.PositiveIntegerField(default=0)
    repeated_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['question_order', 'created_at']
        indexes = [
            models.Index(fields=['session', 'question_order']),
            models.Index(fields=['candidate', 'created_at']),
        ]

    def __str__(self):
        return f'LiveResponse {self.question_order} ({self.status}) for {self.session_id}'


class AiInterviewBugReport(BaseTenantModel):
    session = models.ForeignKey(
        AiInterviewSession, on_delete=models.CASCADE, related_name='bug_reports'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to=bug_report_upload_path, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f'BugReport {self.session_id} - {self.title[:40]}'


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


class TenantRecruitmentSettings(models.Model):
    """Per-tenant recruitment / interview configuration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'core.Tenant', on_delete=models.CASCADE, related_name='recruitment_settings'
    )
    interview_recording_retention_days = models.PositiveIntegerField(default=15)
    live_watch_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recruitment settings: {self.tenant_id}"

    @classmethod
    def get_for_tenant(cls, tenant_id):
        obj, _ = cls.objects.get_or_create(tenant_id=tenant_id)
        return obj


class AiInterviewMediaChunk(models.Model):
    """Live upload chunks during an active interview session."""

    KIND_SESSION_COMPOSITE = 'session_composite'
    KIND_CAMERA = 'camera'
    KIND_CHOICES = [
        (KIND_SESSION_COMPOSITE, 'Session composite'),
        (KIND_CAMERA, 'Camera'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AiInterviewSession, on_delete=models.CASCADE, related_name='media_chunks'
    )
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    sequence = models.PositiveIntegerField()
    content_type = models.CharField(max_length=128, default='video/webm')
    data = models.BinaryField()
    byte_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'sequence']
        indexes = [
            models.Index(fields=['session', 'kind', 'sequence']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'kind', 'sequence'],
                name='uniq_interview_chunk_seq',
            ),
        ]

    def __str__(self):
        return f"Chunk {self.kind}#{self.sequence} for {self.session_id}"


class AiInterviewMediaBlob(models.Model):
    """Finalized media artifacts stored in PostgreSQL until S3 is enabled."""

    KIND_SESSION_COMPOSITE = 'session_composite'
    KIND_CAMERA = 'camera'
    KIND_ANSWER_AUDIO = 'answer_audio'
    KIND_PROCTOR_IMAGE = 'proctor_image'
    KIND_ASTRA_TTS = 'astra_tts'
    KIND_CHOICES = [
        (KIND_SESSION_COMPOSITE, 'Session composite'),
        (KIND_CAMERA, 'Camera'),
        (KIND_ANSWER_AUDIO, 'Answer audio'),
        (KIND_PROCTOR_IMAGE, 'Proctor image'),
        (KIND_ASTRA_TTS, 'Astra TTS utterance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AiInterviewSession, on_delete=models.CASCADE, related_name='media_blobs'
    )
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    question_order = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=128, default='application/octet-stream')
    data = models.BinaryField()
    byte_size = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'question_order']
        indexes = [
            models.Index(fields=['session', 'kind']),
        ]

    def __str__(self):
        return f"Blob {self.kind} for {self.session_id}"
