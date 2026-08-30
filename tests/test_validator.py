"""validator 模块的单元测试。"""

import copy
from datetime import date
from pathlib import Path
import unittest

from resume_generator.models import Contact, Entry, FieldError, Name, Section
from resume_generator.validator import (
    load_json,
    parse_json,
    parse_paper_size,
    validate_json,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestValidateJson(unittest.TestCase):
    """验证严格契约、字段路径和模型转换。"""

    def test_valid_resume_fixture_is_valid(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")

        self.assertIsNone(validate_json(data))
        self.assertEqual(parse_paper_size(data), "A4")

    def test_all_supported_paper_sizes_are_valid(self) -> None:
        for paper_size in ("A4", "Letter"):
            with self.subTest(paper_size=paper_size):
                data = load_json(FIXTURES / "valid_resume.json")
                data["paper_size"] = paper_size

                self.assertIsNone(validate_json(data))
                self.assertEqual(parse_paper_size(data), paper_size)

    def test_paper_size_is_required_and_strict(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        del data["paper_size"]
        with self.assertRaisesRegex(FieldError, "root: 缺少字段: paper_size"):
            validate_json(data)

        for invalid_paper_size in ("a4", "letter", "Legal", "en-US", None):
            with self.subTest(paper_size=invalid_paper_size):
                data = load_json(FIXTURES / "valid_resume.json")
                data["paper_size"] = invalid_paper_size
                with self.assertRaisesRegex(FieldError, "paper_size"):
                    validate_json(data)

    def test_legacy_locale_field_is_rejected(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["locale"] = "en-US"

        with self.assertRaisesRegex(FieldError, "root: 存在多余字段: locale"):
            validate_json(data)

    def test_parse_json_uses_only_existing_models(self) -> None:
        name, contacts, sections = parse_json(
            load_json(FIXTURES / "valid_resume.json")
        )

        self.assertIsInstance(name, Name)
        self.assertTrue(all(isinstance(item, Contact) for item in contacts))
        self.assertTrue(all(isinstance(item, Section) for item in sections))
        self.assertTrue(
            all(isinstance(entry, Entry) for section in sections for entry in section.entries)
        )
        first_entry = sections[0].entries[0]
        self.assertEqual(first_entry.start_date, date(2021, 9, 1))
        self.assertEqual(first_entry.end_date, date(2025, 6, 1))
        self.assertEqual(sections[1].entries[0].end_date, "至今")

    def test_parse_json_does_not_mutate_input(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        original = copy.deepcopy(data)

        parse_json(data)

        self.assertEqual(data, original)

    def test_blank_href_does_not_require_label(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["basics"]["contacts"][0] = {"label": "", "href": ""}

        self.assertIsNone(validate_json(data))

    def test_invalid_fixtures_have_precise_field_paths(self) -> None:
        cases = (
            ("invalid_missing_basics.json", "root"),
            ("invalid_date_order.json", "sections[0].entries[0].end_date"),
            ("invalid_bullet_type.json", "sections[0].entries[0].bullets[1]"),
            ("invalid_contact_label.json", "basics.contacts[0].label"),
        )
        for filename, expected_path in cases:
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(FieldError, expected_path.replace("[", r"\[").replace("]", r"\]")):
                    validate_json(load_json(FIXTURES / filename))

    def test_unknown_field_is_rejected(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["basics"]["nickname"] = "不允许"

        with self.assertRaisesRegex(FieldError, "basics: 存在多余字段: nickname"):
            validate_json(data)

    def test_wrong_field_types_are_rejected(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0]["start_date"] = 20210901

        with self.assertRaisesRegex(FieldError, r"sections\[0\].entries\[0\].start_date"):
            validate_json(data)

    def test_invalid_calendar_date_is_not_treated_as_status(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0]["end_date"] = "2025-02-30"

        with self.assertRaisesRegex(
            FieldError,
            r"sections\[0\].entries\[0\].end_date",
        ):
            validate_json(data)

    def test_day_precision_is_rejected(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0]["start_date"] = "2021-09-01"

        with self.assertRaisesRegex(
            FieldError,
            r"sections\[0\].entries\[0\].start_date",
        ):
            validate_json(data)

        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0]["end_date"] = "2025-06-30"

        with self.assertRaisesRegex(
            FieldError,
            r"sections\[0\].entries\[0\].end_date",
        ):
            validate_json(data)

    def test_entry_metadata_is_valid_without_bullets(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        del data["sections"][0]["entries"][0]["bullets"]

        self.assertIsNone(validate_json(data))
        _, _, sections = parse_json(data)
        self.assertEqual(sections[0].entries[0].bullets, [])

    def test_bullets_must_be_a_nonempty_list_of_nonblank_strings(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0]["bullets"] = None

        with self.assertRaisesRegex(
            FieldError,
            r"sections\[0\].entries\[0\].bullets",
        ):
            validate_json(data)

        for value, expected_path in (([], "bullets"), (["   "], "bullets[0]")):
            with self.subTest(value=value):
                data = load_json(FIXTURES / "valid_resume.json")
                data["sections"][0]["entries"][0]["bullets"] = value

                with self.assertRaisesRegex(
                    FieldError,
                    expected_path.replace("[", r"\[").replace("]", r"\]"),
                ):
                    validate_json(data)

    def test_entry_requires_metadata_or_bullets(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"][0]["entries"][0] = {}

        with self.assertRaisesRegex(FieldError, r"sections\[0\].entries\[0\]"):
            validate_json(data)

    def test_sections_require_visible_titles_and_entries(self) -> None:
        cases = (
            ([], "sections"),
            ([{"title": "   ", "entries": [{"title": "经历"}]}], "title"),
            ([{"title": "经历", "entries": []}], "entries"),
        )
        for sections, expected_path in cases:
            with self.subTest(sections=sections):
                data = load_json(FIXTURES / "valid_resume.json")
                data["sections"] = sections

                with self.assertRaisesRegex(FieldError, expected_path):
                    validate_json(data)


if __name__ == "__main__":
    unittest.main()
