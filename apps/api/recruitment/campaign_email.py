"""Outreach emails for recruitment campaigns."""

from __future__ import annotations

from core.email.outbound import send_tenant_email
from recruitment.email_service import get_frontend_base_url
from recruitment.models import Candidate, RecruitmentCampaign


def get_portal_link(candidate: Candidate) -> str:
    return f"{get_frontend_base_url()}/interview/portal/{candidate.portal_token}"


def render_outreach_html(campaign: RecruitmentCampaign, candidate: Candidate) -> str:
    link = get_portal_link(candidate)
    name = candidate.first_name or 'there'
    cta = (
        f'<p style="margin:24px 0;">'
        f'<a href="{link}" style="background:#2563eb;color:#fff;padding:12px 24px;'
        f'text-decoration:none;border-radius:6px;font-weight:bold;">'
        f'Upload resume &amp; continue</a></p>'
    )
    body = campaign.outreach_body_html or ''
    if '{{first_name}}' in body:
        body = body.replace('{{first_name}}', name)
    return f"{body}\n{cta}\n<p style='font-size:12px;color:#666;'>This link stays valid until your interview is completed.</p>"


def send_campaign_outreach(campaign: RecruitmentCampaign, candidate: Candidate, *, connection=None) -> None:
    html = render_outreach_html(campaign, candidate)
    text = campaign.outreach_body_text or html
    subject = campaign.outreach_subject or f'Opportunity: {campaign.title}'
    if '{{first_name}}' in subject:
        subject = subject.replace('{{first_name}}', candidate.first_name or '')
    send_tenant_email(
        tenant_id=campaign.tenant_id,
        to=candidate.email,
        subject=subject,
        body_html=html,
        body_text=text,
        source='recruitment_outreach',
        source_id=str(campaign.id),
    )
