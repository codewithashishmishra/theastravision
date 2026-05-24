"""Download official government PDF templates listed in form_registry.json."""

import json
from pathlib import Path

import requests
from django.core.management.base import BaseCommand

from compliance.pdf_fill import COMPLIANCE_ROOT, REGISTRY_PATH


class Command(BaseCommand):
    help = 'Download government form PDF templates from form_registry.json URLs'

    def add_arguments(self, parser):
        parser.add_argument('--tax-year', type=int, default=None)
        parser.add_argument('--jurisdiction', type=str, default=None)

    def handle(self, *args, **options):
        if not REGISTRY_PATH.exists():
            self.stderr.write('form_registry.json not found')
            return
        entries = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
        tax_year = options.get('tax_year')
        jurisdiction = options.get('jurisdiction')
        for entry in entries:
            if tax_year and entry.get('tax_year') != tax_year:
                continue
            if jurisdiction and entry.get('jurisdiction') != jurisdiction:
                continue
            url = entry.get('source_url', '')
            if not url.endswith('.pdf'):
                self.stdout.write(f'Skip (not direct PDF): {entry["doc_type"]} — {url}')
                continue
            dest = COMPLIANCE_ROOT / entry['template_path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                resp = requests.get(url, timeout=60, headers={'User-Agent': 'AastraaHR/1.0'})
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                self.stdout.write(self.style.SUCCESS(f'Downloaded {dest}'))
            except Exception as exc:
                self.stderr.write(f'Failed {entry["doc_type"]}: {exc}')
