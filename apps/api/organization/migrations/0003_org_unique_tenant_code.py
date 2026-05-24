from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_dedupe_org_codes'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='branch',
            constraint=models.UniqueConstraint(
                fields=('tenant', 'code'), name='uniq_branch_tenant_code'
            ),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(
                fields=('tenant', 'code'), name='uniq_department_tenant_code'
            ),
        ),
        migrations.AddConstraint(
            model_name='designation',
            constraint=models.UniqueConstraint(
                fields=('tenant', 'code'), name='uniq_designation_tenant_code'
            ),
        ),
    ]
