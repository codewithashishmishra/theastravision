import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import FeatureFlag

def seed():
    flags = [
        {"name": "BETA_AI_ASSESSMENT", "description": "Enable AI-driven candidate assessment parsing.", "is_active": True},
        {"name": "EXPERIMENTAL_DARK_MODE", "description": "Enable new experimental dark mode themes.", "is_active": False},
        {"name": "NEW_DASHBOARD_UI", "description": "Toggle the next-generation analytics dashboard.", "is_active": True},
    ]
    for flag in flags:
        obj, created = FeatureFlag.objects.get_or_create(name=flag['name'], defaults=flag)
        if created:
            print(f"Created flag: {obj.name}")
        else:
            print(f"Flag {obj.name} already exists.")

if __name__ == "__main__":
    seed()
