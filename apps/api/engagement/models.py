from django.db import models
from organization.models import BaseTenantModel


class Survey(BaseTenantModel):
    title = models.CharField(max_length=255)
    questions = models.TextField(help_text='JSON array of survey questions')

    def __str__(self):
        return self.title


class Announcement(BaseTenantModel):
    title = models.CharField(max_length=255)
    body = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
