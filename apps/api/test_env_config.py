import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import EnvConfiguration, ConfigSettings

# Clean up previous tests
EnvConfiguration.objects.filter(module='SMTP').delete()

# Create new config
config = EnvConfiguration.objects.create(module='SMTP')
config.set_config({'host': 'smtp.gmail.com', 'port': 587, 'user': 'test@gmail.com'})
config.save()

# Retrieve using LRU cache
retrieved_config = EnvConfiguration.get_cached_config('SMTP')
print("Retrieved Config:", retrieved_config)

# Verify ConfigSettings
key_settings = ConfigSettings.objects.get(name="default_env_key")
print("Key settings created:", key_settings.name)
