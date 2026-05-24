"""List and auto-resolve AcroForm field mappings for government PDF templates."""

from pathlib import Path

from django.core.management.base import BaseCommand

from compliance.dynamic_field_map import (
    list_acroform_field_names,
    resolve_fields_for_form,
    suggest_field_map_json,
)
from compliance.pdf_fill import COMPLIANCE_ROOT, get_registry_entry, load_form_registry, template_path


class Command(BaseCommand):
    help = 'Inspect AcroForm fields and print dynamically resolved field map JSON'

    def add_arguments(self, parser):
        parser.add_argument('doc_type', nargs='?', default='W2')
        parser.add_argument('--jurisdiction', default='US')
        parser.add_argument('--tax-year', type=int, default=2025)
        parser.add_argument('--list-only', action='store_true', help='List raw field names only')
        parser.add_argument('--write-cache', action='store_true', help='Write resolved map to field_maps JSON')

    def handle(self, *args, **options):
        doc_type = options['doc_type'].upper()
        if doc_type == 'W-2':
            doc_type = 'W2'
        jurisdiction = options['jurisdiction']
        tax_year = options['tax_year']

        entry = get_registry_entry(jurisdiction, doc_type, tax_year)
        if not entry:
            for e in load_form_registry():
                if e['jurisdiction'] == jurisdiction and e['doc_type'] == doc_type:
                    entry = e
                    break
        if not entry:
            self.stderr.write(self.style.ERROR(f'No registry entry for {jurisdiction}/{doc_type}'))
            return

        path = template_path(entry)
        if not path.exists():
            self.stderr.write(self.style.ERROR(f'Template missing: {path}'))
            return

        names = list_acroform_field_names(path)
        self.stdout.write(self.style.NOTICE(f'Template: {path.name} ({len(names)} fields)'))

        if options['list_only']:
            for name in names:
                self.stdout.write(name)
            return

        resolved = resolve_fields_for_form(doc_type, path)
        self.stdout.write(self.style.SUCCESS(f'\nResolved {len(resolved)} logical keys:\n'))
        for logical, pdf_field in sorted(resolved.items()):
            short = pdf_field.split('topmostSubform[0].')[-1] if 'topmostSubform' in pdf_field else pdf_field
            self.stdout.write(f'  {logical:24} -> {short}')

        if options['write_cache']:
            rel = entry.get('field_map_path', '')
            cache_path = COMPLIANCE_ROOT / rel
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(suggest_field_map_json(doc_type, path), encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f'\nWrote {cache_path}'))
        else:
            self.stdout.write('\n--- Suggested JSON (use --write-cache to save) ---\n')
            self.stdout.write(suggest_field_map_json(doc_type, path))
