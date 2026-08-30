"""稳定 Python 服务接口的单元测试。"""

import copy
from io import BytesIO
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from docx import Document

from resume_generator import FieldError, render_json_file_to_docx, render_json_to_docx
from resume_generator.validator import load_json

FIXTURES = Path(__file__).parent / "fixtures"


class TestRenderJsonToDocx(unittest.TestCase):
    """验证内存渲染的契约、结构和错误语义。"""

    def test_valid_json_returns_complete_docx_bytes(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")

        result = render_json_to_docx(data)

        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"PK\x03\x04"))
        with ZipFile(BytesIO(result)) as archive:
            names = set(archive.namelist())
        self.assertIn("[Content_Types].xml", names)
        self.assertIn("word/document.xml", names)
        self.assertIn("word/styles.xml", names)
        self.assertIn("word/numbering.xml", names)

        document = Document(BytesIO(result))
        self.assertEqual(document.paragraphs[0].text, "王小明")

    def test_rendering_does_not_mutate_input(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        original = copy.deepcopy(data)

        render_json_to_docx(data)

        self.assertEqual(data, original)

    def test_invalid_json_preserves_field_error(self) -> None:
        data = load_json(FIXTURES / "valid_resume.json")
        data["sections"] = []

        with self.assertRaisesRegex(FieldError, "sections"):
            render_json_to_docx(data)


class TestRenderJsonFileToDocx(unittest.TestCase):
    """验证文件级 Python API 与 CLI 一致的输出语义。"""

    def test_writes_docx_and_returns_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            input_path = temporary_root / "resume.json"
            output_path = temporary_root / "resume.docx"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)

            result = render_json_file_to_docx(input_path, output_path)

            self.assertEqual(result, output_path.resolve())
            self.assertTrue(result.is_file())
            self.assertTrue(result.read_bytes().startswith(b"PK\x03\x04"))

    def test_pdf_option_uses_matching_sibling_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            input_path = temporary_root / "resume.json"
            output_path = temporary_root / "resume.docx"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)

            with patch("resume_generator.service.convert_docx_to_pdf") as convert:
                result = render_json_file_to_docx(
                    input_path,
                    output_path,
                    pdf=True,
                )

            self.assertEqual(result, output_path.resolve())
            convert.assert_called_once_with(
                output_path.resolve(),
                output_path.with_suffix(".pdf").resolve(),
                force=False,
            )

    def test_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            input_path = temporary_root / "resume.json"
            output_path = temporary_root / "resume.docx"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)
            output_path.write_bytes(b"existing")

            with self.assertRaises(FileExistsError):
                render_json_file_to_docx(input_path, output_path)


if __name__ == "__main__":
    unittest.main()
