from django.contrib import admin

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
)

admin.site.register(JobRequisition)
admin.site.register(Candidate)
admin.site.register(Interview)
admin.site.register(AiInterviewSession)
admin.site.register(AiInterviewQuestion)
admin.site.register(AssessmentTemplate)
admin.site.register(AssessmentQuestion)
admin.site.register(AssessmentAttempt)
admin.site.register(ProctorSnapshot)
admin.site.register(AiInterviewReport)
