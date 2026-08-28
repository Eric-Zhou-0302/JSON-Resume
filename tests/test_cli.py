"""命令行入口和退出码测试。"""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from docx import Document
from docx.shared import Inches

from resume_generator.cli import (
    ANSI_LOGO,
    CliReporter,
    DEFAULT_OUTPUT_DIRECTORY,
    main as cli_main,
)

PROJECT_ROOT = Path(__file__).parents[1]
MAIN = PROJECT_ROOT / "main.py"
FIXTURES = Path(__file__).parent / "fixtures"


class _InteractiveBuffer(io.StringIO):
    """模拟支持颜色的交互式终端。"""

    def isatty(self) -> bool:
        return True


class TestCli(unittest.TestCase):
    """通过真实子进程验证用户可见的 CLI 行为。"""

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(MAIN), *arguments],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help(self) -> None:
        result = self._run("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("--force", result.stdout)
        self.assertIn("--pdf", result.stdout)
        self.assertIn("output", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_version(self) -> None:
        result = self._run("--version")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "json-resume 1.0.0\n")
        self.assertEqual(result.stderr, "")

    def test_interactive_reporter_shows_indigo_logo_and_progress(self) -> None:
        output = _InteractiveBuffer()

        with patch.dict("os.environ", {"TERM": "xterm-256color"}, clear=True):
            reporter = CliReporter(
                quiet=False,
                no_banner=False,
                stdout=output,
                stderr=io.StringIO(),
            )
            reporter.start()
            reporter.phase("读取  resume.json")
            reporter.success("已校验  zh-CN · A4 · 4 个栏目")

        rendered = output.getvalue()
        self.assertIn(ANSI_LOGO, rendered)
        self.assertIn("JSON in. Career out.", rendered)
        self.assertIn("读取  resume.json", rendered)
        self.assertIn("已校验  zh-CN · A4 · 4 个栏目", rendered)

    def test_quiet_reporter_keeps_path_only_output(self) -> None:
        output = _InteractiveBuffer()
        document_path = Path("/tmp/resume.docx")
        pdf_path = Path("/tmp/resume.pdf")
        reporter = CliReporter(
            quiet=True,
            no_banner=False,
            stdout=output,
            stderr=io.StringIO(),
        )

        reporter.start()
        reporter.phase("不应显示")
        reporter.complete(document_path, pdf_path)

        self.assertEqual(output.getvalue(), f"{document_path}\n{pdf_path}\n")

    def test_default_output_directory_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            input_path = temporary_root / "resume.json"
            output_directory = temporary_root / "output"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)

            with (
                patch(
                    "resume_generator.cli.DEFAULT_OUTPUT_DIRECTORY",
                    output_directory,
                ),
                redirect_stdout(io.StringIO()),
            ):
                exit_code = cli_main([str(input_path)])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_directory / "resume.docx").is_file())

    def test_success_default_output_overwrite_protection_and_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / f"resume-{Path(directory).name}.json"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)
            output_path = DEFAULT_OUTPUT_DIRECTORY / input_path.with_suffix(
                ".docx"
            ).name
            output_path.unlink(missing_ok=True)

            try:
                first = self._run(str(input_path))
                blocked = self._run(str(input_path))
                forced = self._run(str(input_path), "--force")

                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertTrue(output_path.is_file())
                self.assertIn(str(output_path), first.stdout)
                self.assertEqual(blocked.returncode, 1)
                self.assertIn("--force", blocked.stderr)
                self.assertNotIn("Traceback", blocked.stderr)
                self.assertEqual(forced.returncode, 0, forced.stderr)
            finally:
                output_path.unlink(missing_ok=True)

    def test_missing_input_is_exit_code_two(self) -> None:
        result = self._run("does-not-exist.json")

        self.assertEqual(result.returncode, 2)
        self.assertIn("输入文件不存在", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_json_is_exit_code_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "invalid.json"
            input_path.write_text("{not valid json", encoding="utf-8")

            result = self._run(str(input_path))

            self.assertEqual(result.returncode, 2)
            self.assertIn("错误:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_validation_error_is_exit_code_two(self) -> None:
        result = self._run(str(FIXTURES / "invalid_bullet_type.json"))

        self.assertEqual(result.returncode, 2)
        self.assertIn("sections[0].entries[0].bullets[1]", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_entry_metadata_without_bullets_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = json.loads(
                (FIXTURES / "valid_resume.json").read_text(encoding="utf-8")
            )
            del data["sections"][0]["entries"][0]["bullets"]
            input_path = Path(directory) / "metadata-entry.json"
            output_path = Path(directory) / "metadata-entry.docx"
            input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = self._run(str(input_path), "-o", str(output_path))

            self.assertTrue(output_path.is_file())

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_empty_bullets_is_exit_code_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = json.loads(
                (FIXTURES / "valid_resume.json").read_text(encoding="utf-8")
            )
            data["sections"][0]["entries"][0]["bullets"] = []
            input_path = Path(directory) / "empty-bullets.json"
            input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = self._run(str(input_path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("sections[0].entries[0].bullets", result.stderr)
        self.assertIn("至少需要一项", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_day_precision_is_exit_code_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = json.loads(
                (FIXTURES / "valid_resume.json").read_text(encoding="utf-8")
            )
            data["sections"][0]["entries"][0]["start_date"] = "2021-09-01"
            input_path = Path(directory) / "day-precision.json"
            input_path.write_text(
                json.dumps(data, ensure_ascii=False),
                encoding="utf-8",
            )

            result = self._run(str(input_path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("start_date", result.stderr)
        self.assertIn("YYYY-MM", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_locale_is_exit_code_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = json.loads(
                (FIXTURES / "valid_resume.json").read_text(encoding="utf-8")
            )
            del data["locale"]
            input_path = Path(directory) / "missing-locale.json"
            input_path.write_text(
                json.dumps(data, ensure_ascii=False),
                encoding="utf-8",
            )

            result = self._run(str(input_path))

            self.assertEqual(result.returncode, 2)
            self.assertIn("root: 缺少字段: locale", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_invalid_output_directory_is_exit_code_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "missing" / "resume.docx"

            result = self._run(
                str(FIXTURES / "valid_resume.json"),
                "-o",
                str(output_path),
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("输出目录不存在", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_en_us_generates_letter_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "resume-en-us.docx"

            result = self._run(
                str(FIXTURES / "valid_resume_en_us.json"),
                "-o",
                str(output_path),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            section = Document(output_path).sections[0]
            self.assertAlmostEqual(section.page_width, Inches(8.5), delta=1000)
            self.assertAlmostEqual(section.page_height, Inches(11), delta=1000)

    def test_pdf_export_uses_matching_path_and_reports_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "resume.json"
            output_path = Path(directory) / "resume.docx"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)

            with (
                patch("resume_generator.cli.convert_docx_to_pdf") as convert,
                patch("resume_generator.cli.count_pdf_pages", return_value=1) as count,
                redirect_stdout(io.StringIO()) as output,
            ):
                exit_code = cli_main(
                    [str(input_path), "-o", str(output_path), "--pdf"]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.is_file())
            resolved_output_path = output_path.resolve()
            convert.assert_called_once_with(
                resolved_output_path,
                resolved_output_path.with_suffix(".pdf"),
                force=False,
            )
            count.assert_called_once_with(resolved_output_path.with_suffix(".pdf"))
            self.assertEqual(
                output.getvalue().splitlines(),
                [
                    str(resolved_output_path),
                    str(resolved_output_path.with_suffix(".pdf")),
                ],
            )

    def test_existing_pdf_blocks_pdf_export_before_docx_is_saved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "resume.json"
            output_path = Path(directory) / "resume.docx"
            pdf_path = output_path.with_suffix(".pdf")
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)
            pdf_path.write_bytes(b"existing PDF")

            with patch("sys.stderr", new_callable=io.StringIO) as error_output:
                exit_code = cli_main(
                    [str(input_path), "-o", str(output_path), "--pdf"]
                )

            self.assertEqual(exit_code, 1)
            self.assertFalse(output_path.exists())
            self.assertIn("--force", error_output.getvalue())

    def test_pdf_conversion_failure_is_exit_code_one_after_docx_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "resume.json"
            output_path = Path(directory) / "resume.docx"
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)

            with (
                patch(
                    "resume_generator.cli.convert_docx_to_pdf",
                    side_effect=RuntimeError("Word 不可用"),
                ),
                patch("sys.stderr", new_callable=io.StringIO) as error_output,
            ):
                exit_code = cli_main(
                    [str(input_path), "-o", str(output_path), "--pdf"]
                )

            self.assertEqual(exit_code, 1)
            self.assertTrue(output_path.is_file())
            self.assertIn("Word 不可用", error_output.getvalue())

    def test_force_allows_existing_docx_and_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "resume.json"
            output_path = Path(directory) / "resume.docx"
            pdf_path = output_path.with_suffix(".pdf")
            shutil.copyfile(FIXTURES / "valid_resume.json", input_path)
            output_path.write_bytes(b"existing DOCX")
            pdf_path.write_bytes(b"existing PDF")

            with (
                patch("resume_generator.cli.convert_docx_to_pdf") as convert,
                patch("resume_generator.cli.count_pdf_pages", return_value=1) as count,
                redirect_stdout(io.StringIO()),
            ):
                exit_code = cli_main(
                    [
                        str(input_path),
                        "-o",
                        str(output_path),
                        "--pdf",
                        "--force",
                    ]
                )

            self.assertEqual(exit_code, 0)
            convert.assert_called_once_with(
                output_path.resolve(),
                pdf_path.resolve(),
                force=True,
            )
            count.assert_called_once_with(pdf_path.resolve())


if __name__ == "__main__":
    unittest.main()
