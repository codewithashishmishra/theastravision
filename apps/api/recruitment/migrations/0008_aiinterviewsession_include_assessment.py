from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0007_interview_portal_enhancements'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiinterviewsession',
            name='include_assessment',
            field=models.BooleanField(
                default=False,
                help_text='When true, candidate receives online assessment after passing voice interview.',
            ),
        ),
    ]
