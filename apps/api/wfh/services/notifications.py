from notifications.models import Notification
from wfh.models import WFHRequest


def notify_wfh_event(request_obj: WFHRequest, event: str):
    employee = request_obj.employee
    if not employee.user_id:
        return
    titles = {
        "submitted": "WFH Request Submitted",
        "manager_approved": "WFH Request — Manager Approved",
        "hr_approved": "WFH Request Approved",
        "rejected": "WFH Request Rejected",
    }
    messages = {
        "submitted": f"Your WFH request for {request_obj.start_date} - {request_obj.end_date} was submitted.",
        "manager_approved": "Your manager approved your WFH request. Awaiting HR if required.",
        "hr_approved": "Your WFH request is fully approved. You may start the desktop tracker.",
        "rejected": f"Your WFH request was rejected. {request_obj.remarks}",
    }
    Notification.objects.create(
        tenant=request_obj.tenant,
        user=employee.user,
        title=titles.get(event, "WFH Update"),
        message=messages.get(event, "WFH request updated."),
        channel="In-App",
    )
    if event == "submitted" and employee.reporting_manager and employee.reporting_manager.user_id:
        Notification.objects.create(
            tenant=request_obj.tenant,
            user=employee.reporting_manager.user,
            title="WFH Approval Required",
            message=f"{employee.first_name} {employee.last_name} submitted a WFH request.",
            channel="In-App",
        )
