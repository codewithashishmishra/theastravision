from pathlib import Path
from unittest import TestCase

from compliance.dynamic_field_map import (
    build_acroform_values,
    expand_data_for_form,
    load_or_resolve_field_map,
    resolve_fields_for_form,
)
from compliance.pdf_fill import fill_government_pdf, get_registry_entry, load_form_registry, template_path


class FormRegistryTests(TestCase):
    def test_registry_has_all_regions(self):
        entries = load_form_registry()
        types = {(e['jurisdiction'], e['doc_type']) for e in entries}
        self.assertIn(('IN', 'FORM16'), types)
        self.assertIn(('US', 'W2'), types)
        self.assertIn(('CA', 'T4'), types)

    def test_get_registry_entry(self):
        entry = get_registry_entry('US', 'W2', 2025)
        self.assertIsNotNone(entry)
        self.assertIn('irs.gov', entry['source_url'])


class DynamicW2FieldMapTests(TestCase):
    def setUp(self):
        self.entry = get_registry_entry('US', 'W2', 2025)
        self.template = template_path(self.entry)

    def test_resolve_w2_fields_when_template_present(self):
        if not self.template.exists():
            self.skipTest('W2 template not downloaded')
        resolved = resolve_fields_for_form('W2', self.template)
        self.assertIn('box1_wages', resolved)
        self.assertIn('employer_name', resolved)
        self.assertTrue(resolved['box1_wages'].endswith('[0]'))

    def test_load_or_resolve_caches_fields(self):
        if not self.template.exists():
            self.skipTest('W2 template not downloaded')
        config = load_or_resolve_field_map(self.entry, self.template)
        self.assertTrue(config.get('fields'))
        self.assertTrue(config.get('dynamic'))

    def test_build_acroform_values_splits_employee_name(self):
        field_map = {
            'employer_name': 'emp_field',
            'box1_wages': 'box1_field',
            'employee_first_name': 'fn_field',
            'employee_last_name': 'ln_field',
        }
        data = {'employer_name': 'Acme', 'employee_name': 'Jane Doe', 'box1_wages': '50000'}
        expanded = expand_data_for_form('W2', data)
        self.assertEqual(expanded['employee_first_name'], 'Jane')
        self.assertEqual(expanded['employee_last_name'], 'Doe')
        acro = build_acroform_values('W2', field_map, data)
        self.assertEqual(acro['fn_field'], 'Jane')
        self.assertEqual(acro['ln_field'], 'Doe')


class PdfFillComplianceTests(TestCase):
    def test_html_fallback_without_template(self):
        pdf, meta = fill_government_pdf(
            'IN',
            'FORM16',
            2099,
            {},
            ['Line 1'],
            'Form 16',
        )
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertEqual(meta['fill_strategy'], 'html_fallback')

    def test_w2_acroform_when_template_downloaded(self):
        entry = get_registry_entry('US', 'W2', 2025)
        template = template_path(entry)
        if not template.exists():
            self.skipTest('W2 template not downloaded')
        pdf, meta = fill_government_pdf(
            'US',
            'W2',
            2025,
            {
                'employer_name': 'Acme Corp',
                'employer_ein': '12-3456789',
                'employee_name': 'John Smith',
                'box1_wages': '75000.00',
                'box2_federal_tax': '12000.00',
                'box4_ss_tax': '4650.00',
                'box6_medicare_tax': '1087.50',
            },
            ['fallback'],
            'W-2',
        )
        self.assertTrue(pdf.startswith(b'%PDF'))
        if meta.get('fill_strategy') == 'acroform':
            self.assertGreater(len(meta.get('fields_filled', [])), 0)
