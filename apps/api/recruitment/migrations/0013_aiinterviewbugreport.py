from django.db import migrations, models
import recruitment.models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0012_candidateprebakedquestion_candidateliveresponse_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AiInterviewBugReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                (
                    'image',
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=recruitment.models.bug_report_upload_path,
                    ),
                ),
                (
                    'session',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='bug_reports',
                        to='recruitment.aiinterviewsession',
                    ),
                ),
                (
                    'tenant',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)s_set',
                        to='core.tenant',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='aiinterviewbugreport',
            index=models.Index(fields=['session', 'created_at'], name='recruitment_ai_sessio_1262f0_idx'),
        ),
    ]
