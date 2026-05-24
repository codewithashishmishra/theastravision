from collections import defaultdict

from django.db import migrations


def _dedupe_model(apps, model_name, fk_updates):
    Model = apps.get_model('organization', model_name)
    groups = defaultdict(list)
    for row in Model.objects.all().order_by('created_at'):
        key = (row.tenant_id, (row.code or '').upper())
        groups[key].append(row)

    for rows in groups.values():
        if len(rows) <= 1:
            continue
        canonical = rows[0]
        duplicate_ids = [r.id for r in rows[1:]]
        for app_label, fk_model, fk_field in fk_updates:
            FKModel = apps.get_model(app_label, fk_model)
            FKModel.objects.filter(**{f'{fk_field}_id__in': duplicate_ids}).update(
                **{fk_field: canonical}
            )
        if model_name == 'Department':
            Model.objects.filter(parent_id__in=duplicate_ids).update(parent=canonical)
        Model.objects.filter(id__in=duplicate_ids).delete()


def dedupe_org_codes(apps, schema_editor):
    _dedupe_model(
        apps,
        'Department',
        [
            ('employees', 'Employee', 'department'),
            ('recruitment', 'JobRequisition', 'department'),
        ],
    )
    _dedupe_model(apps, 'Branch', [])
    _dedupe_model(apps, 'Designation', [])


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('employees', '0001_initial'),
        ('recruitment', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(dedupe_org_codes, migrations.RunPython.noop),
    ]
