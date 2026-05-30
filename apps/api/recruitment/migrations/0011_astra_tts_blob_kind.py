# Adds astra_tts choice (CharField — no schema change required)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0010_rename_recruit_blob_sess_kind_recruitment_session_00f523_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiinterviewmediablob',
            name='kind',
            field=models.CharField(
                choices=[
                    ('session_composite', 'Session composite'),
                    ('camera', 'Camera'),
                    ('answer_audio', 'Answer audio'),
                    ('proctor_image', 'Proctor image'),
                    ('astra_tts', 'Astra TTS utterance'),
                ],
                max_length=32,
            ),
        ),
    ]
