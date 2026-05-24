from django.utils import timezone
from rest_framework.exceptions import ValidationError

from wfh.models import WFHApproval, WFHPolicy, WFHRequest
from wfh.services.notifications import notify_wfh_event


def manager_approve(request_obj: WFHRequest, actor, remarks=""):
    if request_obj.status != WFHRequest.STATUS_PENDING:
        raise ValidationError("Request is not pending manager approval.")
    policy = WFHPolicy.get_active(request_obj.tenant_id)
    request_obj.approved_by_manager = actor
    if policy and policy.require_hr_approval:
        request_obj.status = WFHRequest.STATUS_MANAGER_APPROVED
    else:
        request_obj.status = WFHRequest.STATUS_HR_APPROVED
        request_obj.approval_date = timezone.now()
    request_obj.remarks = remarks or request_obj.remarks
    request_obj.save()
    WFHApproval.objects.create(
        tenant=request_obj.tenant,
        wfh_request=request_obj,
        actor=actor,
        action="manager_approve",
        remarks=remarks,
    )
    notify_wfh_event(request_obj, "manager_approved")
    return request_obj


def hr_approve(request_obj: WFHRequest, actor, remarks=""):
    if request_obj.status not in (WFHRequest.STATUS_PENDING, WFHRequest.STATUS_MANAGER_APPROVED):
        raise ValidationError("Request is not eligible for HR approval.")
    request_obj.approved_by_hr = actor
    request_obj.status = WFHRequest.STATUS_HR_APPROVED
    request_obj.approval_date = timezone.now()
    request_obj.remarks = remarks or request_obj.remarks
    request_obj.save()
    WFHApproval.objects.create(
        tenant=request_obj.tenant,
        wfh_request=request_obj,
        actor=actor,
        action="hr_approve",
        remarks=remarks,
    )
    notify_wfh_event(request_obj, "hr_approved")
    return request_obj


def reject_request(request_obj: WFHRequest, actor, remarks=""):
    if request_obj.status in (WFHRequest.STATUS_REJECTED, WFHRequest.STATUS_CANCELLED):
        raise ValidationError("Request already closed.")
    request_obj.status = WFHRequest.STATUS_REJECTED
    request_obj.remarks = remarks
    request_obj.save()
    WFHApproval.objects.create(
        tenant=request_obj.tenant,
        wfh_request=request_obj,
        actor=actor,
        action="reject",
        remarks=remarks,
    )
    notify_wfh_event(request_obj, "rejected")
    return request_obj


def cancel_request(request_obj: WFHRequest, actor, remarks=""):
    if request_obj.status != WFHRequest.STATUS_PENDING:
        raise ValidationError("Only pending requests can be cancelled.")
    request_obj.status = WFHRequest.STATUS_CANCELLED
    request_obj.remarks = remarks
    request_obj.save()
    WFHApproval.objects.create(
        tenant=request_obj.tenant,
        wfh_request=request_obj,
        actor=actor,
        action="cancel",
        remarks=remarks,
    )
    return request_obj
