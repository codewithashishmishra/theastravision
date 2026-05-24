from django.core.management.base import BaseCommand

from compliance.rule_seeds import seed_statutory_rules


class Command(BaseCommand):
    help = 'Seed statutory payroll rules for IN, US, CA'

    def handle(self, *args, **options):
        seed_statutory_rules()
        self.stdout.write(self.style.SUCCESS('Statutory rules seeded.'))
