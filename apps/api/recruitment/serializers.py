from rest_framework import serializers

from .models import (
    AiInterviewBugReport,
    AiInterviewQuestion,
    AiInterviewReport,
    AiInterviewSession,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentTemplate,
    Candidate,
    Interview,
    JobRequisition,
    ProctorSnapshot,
    RecruitmentCampaign,
    TenantCareerPortalSettings,
    TenantRecruitmentSettings,
)
from .campaign_services import campaign_stats
from employees.models import Employee

from .job_board_utils import sanitize_job_html


class JobRequisitionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = JobRequisition
        fields = '__all__'
        read_only_fields = ('published_at',)

    def validate_rich_description_html(self, value):
        return sanitize_job_html(value or '')


class TenantRecruitmentSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantRecruitmentSettings
        fields = [
            'id',
            'interview_recording_retention_days',
            'live_watch_enabled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class CareerPortalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantCareerPortalSettings
        fields = [
            'id',
            'slug',
            'api_key_prefix',
            'allowed_embed_origins',
            'logo_url',
            'primary_color',
            'company_blurb',
            'custom_domain',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('api_key_prefix', 'created_at', 'updated_at')


class CandidateSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    match_passed = serializers.SerializerMethodField()
    proposed_reporting_manager_name = serializers.SerializerMethodField()
    has_active_session = serializers.SerializerMethodField()
    has_interview_scheduled = serializers.SerializerMethodField()
    campaign_title = serializers.CharField(source='campaign.title', read_only=True, allow_null=True)

    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = (
            'parsed_resume_text',
            'match_breakdown',
            'ai_match_score',
            'portal_token',
            'outreach_status',
            'outreach_sent_at',
        )

    def get_has_active_session(self, obj):
        return obj.ai_sessions.exclude(status__in=('completed', 'failed', 'expired')).exists()

    def get_has_interview_scheduled(self, obj):
        return obj.ai_sessions.exists()

    def get_match_passed(self, obj):
        return obj.ai_match_score >= (obj.job.match_threshold or 70)

    def get_proposed_reporting_manager_name(self, obj):
        mgr = obj.proposed_reporting_manager
        if mgr:
            return f'{mgr.first_name} {mgr.last_name}'.strip()
        return None

    def validate(self, attrs):
        tenant_id = self.context.get('tenant_id')
        manager = attrs.get('proposed_reporting_manager')
        if self.instance is None and not manager:
            raise serializers.ValidationError(
                {'proposed_reporting_manager': 'Future reporting manager is required.'}
            )
        if manager and tenant_id:
            if str(manager.tenant_id) != str(tenant_id):
                raise serializers.ValidationError(
                    {'proposed_reporting_manager': 'Manager must belong to the same organization.'}
                )
            if manager.status != 'Active':
                raise serializers.ValidationError(
                    {'proposed_reporting_manager': 'Future reporting manager must be an active employee.'}
                )
        return attrs


class RecruitmentCampaignListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentCampaign
        fields = [
            'id',
            'title',
            'status',
            'job',
            'job_title',
            'send_rate_per_minute',
            'created_at',
            'stats',
        ]

    def get_stats(self, obj):
        return campaign_stats(obj)


class RecruitmentCampaignDetailSerializer(RecruitmentCampaignListSerializer):
    class Meta(RecruitmentCampaignListSerializer.Meta):
        fields = RecruitmentCampaignListSerializer.Meta.fields + [
            'outreach_subject',
            'outreach_body_html',
            'outreach_body_text',
            'default_reporting_manager',
            'created_by',
        ]


class InterviewSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.first_name', read_only=True)
    interviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = '__all__'

    def get_interviewer_name(self, obj):
        return obj.interviewer.first_name if obj.interviewer else 'TBD'


class AiInterviewQuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiInterviewQuestion
        fields = ('id', 'order', 'question_text')


class AiInterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiInterviewQuestion
        fields = '__all__'


class AiInterviewSessionSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    magic_link = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()

    class Meta:
        model = AiInterviewSession
        fields = '__all__'

    def get_candidate_name(self, obj):
        return f"{obj.candidate.first_name} {obj.candidate.last_name}"

    def get_magic_link(self, obj):
        from .services import get_magic_link
        return get_magic_link(obj)

    def get_report_id(self, obj):
        report = getattr(obj, 'report', None)
        return str(report.id) if report else None


class AiInterviewSessionPublicSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    question_count = serializers.SerializerMethodField()
    include_assessment = serializers.BooleanField(read_only=True)

    class Meta:
        model = AiInterviewSession
        fields = (
            'id', 'status', 'candidate_name', 'job_title', 'expires_at',
            'current_question_index', 'question_count', 'include_assessment',
        )

    def get_candidate_name(self, obj):
        return obj.candidate.first_name

    def get_question_count(self, obj):
        return obj.job.interview_question_count


class AssessmentQuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = ('id', 'order', 'prompt', 'option_a', 'option_b', 'option_c', 'option_d')


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = '__all__'


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentTemplate
        fields = '__all__'


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = '__all__'


class ProctorSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctorSnapshot
        fields = '__all__'


class AiInterviewReportSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='session.job.title', read_only=True)
    session_status = serializers.CharField(source='session.status', read_only=True)
    match_score = serializers.IntegerField(source='session.candidate.ai_match_score', read_only=True)
    voice_score = serializers.FloatField(source='session.overall_voice_score', read_only=True)
    assessment_score = serializers.FloatField(source='session.assessment_score', read_only=True)
    created_at = serializers.DateTimeField(source='session.created_at', read_only=True)

    class Meta:
        model = AiInterviewReport
        fields = '__all__'

    def get_candidate_name(self, obj):
        c = obj.session.candidate
        return f"{c.first_name} {c.last_name}"


class AiInterviewBugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiInterviewBugReport
        fields = ('id', 'session', 'title', 'description', 'image', 'created_at')
        read_only_fields = ('id', 'created_at')
