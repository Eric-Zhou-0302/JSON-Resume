"""DOCX 的 PDF 导出与 PDF 页数检测。"""

import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path

PDF_OUTPUT_TIMEOUT_SECONDS = 10.0
PDF_OUTPUT_POLL_INTERVAL_SECONDS = 0.1


def convert_docx_to_pdf(
    docx_path: Path,
    pdf_path: Path,
    *,
    force: bool = False,
) -> None:
    """使用 docx2pdf 通过 Microsoft Word 导出同名 PDF。"""
    if not docx_path.is_file():
        raise FileNotFoundError(f"DOCX 文件不存在: {docx_path}")
    if not pdf_path.parent.is_dir():
        raise NotADirectoryError(f"输出目录不存在: {pdf_path.parent}")
    if pdf_path.exists() and not force:
        raise FileExistsError(
            f"PDF 输出文件已存在；如需覆盖请使用 --force: {pdf_path}"
        )

    try:
        from docx2pdf import convert
    except ImportError as error:
        raise RuntimeError(
            "缺少 PDF 导出依赖；请使用项目 requirements.txt 安装 docx2pdf"
        ) from error

    try:
        convert(str(docx_path), str(pdf_path))
    except SystemExit as error:
        raise RuntimeError(
            "DOCX 转 PDF 失败：Microsoft Word 未能完成自动化导出"
        ) from error
    except Exception as error:
        raise RuntimeError(f"DOCX 转 PDF 失败: {error}") from error

    if not _wait_for_pdf_output(pdf_path):
        raise RuntimeError(f"DOCX 转 PDF 未生成有效文件: {pdf_path}")


def _wait_for_pdf_output(pdf_path: Path) -> bool:
    """等待 Word 自动化完成异步 PDF 落盘，避免返回过早导致的误报。"""
    deadline = time.monotonic() + PDF_OUTPUT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if pdf_path.is_file() and pdf_path.stat().st_size > 0:
            return True
        time.sleep(PDF_OUTPUT_POLL_INTERVAL_SECONDS)
    return pdf_path.is_file() and pdf_path.stat().st_size > 0


def count_pdf_pages(pdf_path: Path) -> int:
    """返回有效 PDF 的实际页数。"""
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError(
            "缺少 PDF 页数检测依赖；请使用项目 requirements.txt 安装 pypdf"
        ) from error

    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as error:
        raise RuntimeError(f"无法读取 PDF 页数: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    """输出 PDF 页数，供人工或 Agent 验收调用。"""
    parser = argparse.ArgumentParser(
        prog="json-resume-pdf-pages",
        description="输出 PDF 的实际页数。",
    )
    parser.add_argument("pdf", type=Path, help="待检测的 PDF 文件")
    arguments = parser.parse_args(argv)

    try:
        print(count_pdf_pages(arguments.pdf.expanduser().resolve()))
    except Exception as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
