from rest_framework import serializers

from .models import (
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
    TenantCareerPortalSettings,
)
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

    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = ('parsed_resume_text', 'match_breakdown', 'ai_match_score')

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

    class Meta:
        model = AiInterviewSession
        fields = '__all__'

    def get_candidate_name(self, obj):
        return f"{obj.candidate.first_name} {obj.candidate.last_name}"

    def get_magic_link(self, obj):
        from .services import get_magic_link
        return get_magic_link(obj)


class AiInterviewSessionPublicSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    question_count = serializers.SerializerMethodField()
    assessment_enabled = serializers.BooleanField(source='job.assessment_enabled')

    class Meta:
        model = AiInterviewSession
        fields = (
            'id', 'status', 'candidate_name', 'job_title', 'expires_at',
            'current_question_index', 'question_count', 'assessment_enabled',
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
