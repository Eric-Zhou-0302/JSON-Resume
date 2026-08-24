"""PDF 导出辅助功能测试。"""

from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from pypdf import PdfWriter

from resume_generator.pdf import convert_docx_to_pdf, count_pdf_pages, main as pdf_main


class TestPdfPageCount(unittest.TestCase):
    """验证 PDF 页数读取独立于视觉验收工具。"""

    def test_count_pdf_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "two-pages.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            writer.add_blank_page(width=595, height=842)
            with pdf_path.open("wb") as stream:
                writer.write(stream)

            self.assertEqual(count_pdf_pages(pdf_path), 2)

    def test_page_count_command_prints_only_the_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "one-page.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            with pdf_path.open("wb") as stream:
                writer.write(stream)

            from contextlib import redirect_stdout
            import io

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = pdf_main([str(pdf_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "1\n")

    def test_missing_pdf_raises_precise_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing.pdf"

            with self.assertRaisesRegex(FileNotFoundError, "PDF 文件不存在"):
                count_pdf_pages(missing_path)

    def test_docx2pdf_system_exit_becomes_a_clear_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            docx_path = Path(directory) / "resume.docx"
            pdf_path = Path(directory) / "resume.pdf"
            docx_path.write_bytes(b"placeholder")

            with patch("docx2pdf.convert", side_effect=SystemExit(1)):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Microsoft Word 未能完成自动化导出",
                ):
                    convert_docx_to_pdf(docx_path, pdf_path)

    def test_pdf_output_can_arrive_shortly_after_word_returns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            docx_path = Path(directory) / "resume.docx"
            pdf_path = Path(directory) / "resume.pdf"
            docx_path.write_bytes(b"placeholder")
            writer_thread: threading.Thread | None = None

            def delayed_convert(*_args: object) -> None:
                nonlocal writer_thread

                def write_pdf() -> None:
                    time.sleep(0.01)
                    pdf_path.write_bytes(b"PDF")

                writer_thread = threading.Thread(target=write_pdf)
                writer_thread.start()

            with patch("docx2pdf.convert", side_effect=delayed_convert):
                convert_docx_to_pdf(docx_path, pdf_path)

            self.assertIsNotNone(writer_thread)
            writer_thread.join()
            self.assertGreater(pdf_path.stat().st_size, 0)
