from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_authsession_ip_address_authsession_location_city_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="authsession",
            name="client_type",
            field=models.CharField(
                choices=[("web", "Web Browser"), ("tracker", "Desktop Tracker")],
                default="web",
                max_length=20,
            ),
        ),
    ]
