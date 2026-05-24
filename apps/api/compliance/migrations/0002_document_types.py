from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compliancedocument',
            name='document_type',
            field=models.CharField(
                choices=[
                    ('FORM16', 'Form 16'),
                    ('FORM12BA', 'Form 12BA'),
                    ('W2', 'W-2'),
                    ('FORM1095C', 'Form 1095-C'),
                    ('T4', 'T4'),
                    ('RL1', 'RL-1'),
                    ('ECR', 'ECR Export'),
                    ('FORM941', 'Form 941 Export'),
                    ('ITR_ASSIST', 'ITR Assist'),
                    ('US_1040_PREP', 'US 1040 Prep'),
                    ('CA_T1_PREP', 'CA T1 Prep'),
                ],
                max_length=20,
            ),
        ),
    ]
