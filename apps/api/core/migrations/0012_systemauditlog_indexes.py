# Generated manually for SystemAuditLog indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_featureflag"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="systemauditlog",
            index=models.Index(fields=["tenant", "created_at"], name="core_sal_tenant_created_idx"),
        ),
        migrations.AddIndex(
            model_name="systemauditlog",
            index=models.Index(fields=["module", "created_at"], name="core_sal_module_created_idx"),
        ),
    ]
