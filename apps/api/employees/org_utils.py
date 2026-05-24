"""Reporting hierarchy helpers for employees."""

from __future__ import annotations

AVATAR_DOCUMENT_TYPES = ('Photo', 'Profile Photo', 'Avatar')


def employee_initials(first_name: str, last_name: str) -> str:
    parts = []
    if first_name:
        parts.append(first_name.strip()[0].upper())
    if last_name:
        parts.append(last_name.strip()[0].upper())
    return ''.join(parts) or '?'


def employee_display_name(employee) -> str:
    return f'{employee.first_name} {employee.last_name}'.strip()


def role_names_for_employee(employee) -> str:
    user = getattr(employee, 'user', None)
    if not user:
        return ''
    mappings = getattr(user, '_prefetched_objects_cache', {}).get('role_mappings')
    if mappings is not None:
        names = [m.role.name for m in mappings if m.role]
    else:
        names = list(
            user.role_mappings.select_related('role').values_list('role__name', flat=True)
        )
    return ', '.join(n for n in names if n)


def avatar_url_for_employee(employee) -> str | None:
    docs = getattr(employee, '_prefetched_objects_cache', {}).get('documents')
    if docs is not None:
        for doc in docs:
            if doc.document_type in AVATAR_DOCUMENT_TYPES and doc.file:
                return doc.file.url
        return None
    doc = (
        employee.documents.filter(document_type__in=AVATAR_DOCUMENT_TYPES)
        .exclude(file='')
        .first()
    )
    if doc and doc.file:
        return doc.file.url
    return None


def reporting_manager_would_cycle(employee_id, manager_id) -> bool:
    if not manager_id or not employee_id:
        return False
    if str(manager_id) == str(employee_id):
        return True
    from employees.models import Employee

    current_id = manager_id
    visited = set()
    while current_id:
        if str(current_id) == str(employee_id):
            return True
        if current_id in visited:
            return True
        visited.add(current_id)
        current_id = (
            Employee.objects.filter(pk=current_id)
            .values_list('reporting_manager_id', flat=True)
            .first()
        )
    return False


def build_org_tree_nodes(employees) -> tuple[list[dict], int]:
    """Build forest of org nodes from a queryset/list of employees."""
    by_id: dict = {}
    children_map: dict = {}

    for emp in employees:
        roles = role_names_for_employee(emp)
        node = {
            'id': str(emp.id),
            'name': employee_display_name(emp),
            'initials': employee_initials(emp.first_name, emp.last_name),
            'role': roles.split(', ')[0] if roles else '',
            'designation': emp.designation.name if emp.designation_id and emp.designation else '',
            'avatar_url': avatar_url_for_employee(emp),
            'employee_code': emp.employee_code,
            'children': [],
        }
        by_id[str(emp.id)] = node
        mgr_id = str(emp.reporting_manager_id) if emp.reporting_manager_id else None
        children_map.setdefault(mgr_id, []).append(str(emp.id))

    roots = []
    for emp in employees:
        emp_id = str(emp.id)
        if emp.reporting_manager_id and str(emp.reporting_manager_id) in by_id:
            parent = by_id[str(emp.reporting_manager_id)]
            parent['children'].append(by_id[emp_id])
        else:
            roots.append(by_id[emp_id])

    return roots, len(employees)
