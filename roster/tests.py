import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from .views import extract_staff_record_from_row, generate_rotation_shift_code


class ExtractStaffRecordTests(SimpleTestCase):
    def test_extracts_name_and_staff_id_from_structured_row(self):
        row = [
            'No. Staf',
            '1234',
            'Nama Penuh',
            'MUHAMMAD ALI BIN AHMAD',
            'No. KP',
            '900101-01-5555',
            'Kumpulan',
            'Kumpulan A',
        ]

        result = extract_staff_record_from_row(row)

        self.assertIsNotNone(result)
        self.assertEqual(result['staff_id'], '1234')
        self.assertEqual(result['name'], 'MUHAMMAD ALI BIN AHMAD')
        self.assertEqual(result['ic_number'], '900101-01-5555')
        self.assertEqual(result['staff_group'], 'Kumpulan A')

    def test_extracts_id_and_name_even_when_row_has_extra_header_noise(self):
        row = [
            'Senarai Anggota',
            'Kumpulan B',
            '000145',
            'SITI NUR AISYAH BINTI HASSAN',
            '800202-02-4444',
            'POLIS',
            'PBT',
        ]

        result = extract_staff_record_from_row(row)

        self.assertIsNotNone(result)
        self.assertEqual(result['staff_id'], '000145')
        self.assertEqual(result['name'], 'SITI NUR AISYAH BINTI HASSAN')

    def test_extracts_simple_two_cell_staff_row(self):
        row = ['123456', 'MUHAMMAD ALI BIN AHMAD']

        result = extract_staff_record_from_row(row)

        self.assertIsNotNone(result)
        self.assertEqual(result['staff_id'], '123456')
        self.assertEqual(result['name'], 'MUHAMMAD ALI BIN AHMAD')

    def test_rotation_puts_leave_before_and_after_night_shift(self):
        officer = SimpleNamespace(staff_group='Kumpulan A', shift_type='ROT')
        first_date = datetime.date(2026, 9, 1)

        self.assertEqual(generate_rotation_shift_code(officer, 4, first_date), 'X')
        self.assertEqual(generate_rotation_shift_code(officer, 5, first_date), '1')
        self.assertEqual(generate_rotation_shift_code(officer, 6, first_date), 'X')

    def test_morning_only_staff_stays_on_morning_shift(self):
        officer = SimpleNamespace(staff_group='MORNING ONLY', shift_type='ROT')
        first_date = datetime.date(2026, 9, 1)

        self.assertEqual(generate_rotation_shift_code(officer, 0, first_date), '2')
        self.assertEqual(generate_rotation_shift_code(officer, 2, first_date), '2')

    def test_afternoon_only_staff_stays_on_afternoon_shift(self):
        officer = SimpleNamespace(staff_group='AFTERNOON ONLY', shift_type='ROT')
        first_date = datetime.date(2026, 9, 1)

        self.assertEqual(generate_rotation_shift_code(officer, 0, first_date), '3')
        self.assertEqual(generate_rotation_shift_code(officer, 2, first_date), '3')
