"""JSON-Resume 的命令行接口。"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from . import __version__
from .models import FieldError
from .pdf import count_pdf_pages
from .service import render_json_file_to_docx

LOGO = """
     ██╗███████╗ ██████╗ ███╗   ██╗
     ██║██╔════╝██╔═══██╗████╗  ██║
     ██║███████╗██║   ██║██╔██╗ ██║
██   ██║╚════██║██║   ██║██║╚██╗██║
╚█████╔╝███████║╚██████╔╝██║ ╚████║
 ╚════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
             R E S U M E
""".strip("\n")

ANSI_RESET = "\033[0m"
ANSI_LOGO = "\033[38;2;139;92;246m"
ANSI_SUCCESS = "\033[38;2;52;211;153m"
ANSI_ERROR = "\033[38;2;251;113;133m"
ANSI_MUTED = "\033[38;2;148;163;184m"


class CliReporter:
    """为终端用户显示进度，同时保留脚本可解析的纯文本输出。"""

    def __init__(
        self,
        *,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr
        self.interactive = self.stdout.isatty()
        self.color_enabled = self.interactive and _color_is_supported()

    def start(self) -> None:
        """在交互式终端显示一次品牌标识。"""
        if not self.interactive:
            return
        print(file=self.stdout)
        print(self._color(LOGO, ANSI_LOGO), file=self.stdout)
        print(
            self._color("             JSON in. Career out.", ANSI_MUTED),
            file=self.stdout,
        )
        print(file=self.stdout)

    def phase(self, message: str) -> None:
        if self.interactive:
            print(f"  {self._color('•', ANSI_MUTED)} {message}", file=self.stdout)

    def success(self, message: str) -> None:
        if self.interactive:
            print(f"  {self._color('✓', ANSI_SUCCESS)} {message}", file=self.stdout)

    def complete(self, output_path: Path, pdf_path: Path | None) -> None:
        """按终端类型输出可读摘要或兼容旧行为的文件路径。"""
        if not self.interactive:
            print(output_path, file=self.stdout)
            if pdf_path is not None:
                print(pdf_path, file=self.stdout)
            return

        print(file=self.stdout)
        print("  完成。", file=self.stdout)

    def error(self, error: BaseException) -> None:
        if not self.interactive:
            print(f"错误: {error}", file=self.stderr)
            return

        print(file=self.stderr)
        print(
            f"  {self._color('✗', ANSI_ERROR)} 无法生成简历",
            file=self.stderr,
        )
        print(file=self.stderr)
        print(f"    {error}", file=self.stderr)
        print(file=self.stderr)
        print("  修正输入或输出设置后重试。", file=self.stderr)

    def _color(self, text: str, color: str) -> str:
        if not self.color_enabled:
            return text
        return f"{color}{text}{ANSI_RESET}"


def _color_is_supported() -> bool:
    """尊重终端能力和 NO_COLOR 约定，避免在日志中留下转义符。"""
    return os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ


def _display_path(path: Path) -> str:
    """优先显示相对当前目录的路径，外部路径则保持绝对路径。"""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    """创建不含业务逻辑的参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="json-resume",
        description="把符合严格 JSON 契约的内容渲染为 DOCX 简历。",
    )
    parser.add_argument("input", type=Path, help="输入 JSON 文件")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="显示版本号并退出",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="输出 DOCX；默认写入当前工作目录的 output 目录并与输入文件同名",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="允许覆盖已经存在的输出文件",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="DOCX 保存成功后，额外导出同名 PDF（默认不导出）",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """运行 CLI，并为可预期错误返回稳定退出码。"""
    arguments = build_parser().parse_args(argv)
    reporter = CliReporter()
    reporter.start()
    input_path = arguments.input.expanduser().resolve()

    try:
        reporter.phase(f"读取  {_display_path(input_path)}")
        reporter.phase("校验并渲染  DOCX 版式")
        output_path = render_json_file_to_docx(
            input_path,
            arguments.output,
            pdf=arguments.pdf,
            force=arguments.force,
        )
    except (FileNotFoundError, PermissionError, UnicodeError, json.JSONDecodeError) as error:
        reporter.error(error)
        return 2
    except FieldError as error:
        reporter.error(error)
        return 2
    except Exception as error:
        reporter.error(error)
        return 1

    try:
        reporter.success(f"已保存  {_display_path(output_path)}")
        pdf_path = output_path.with_suffix(".pdf") if arguments.pdf else None
        if pdf_path is not None:
            page_count = count_pdf_pages(pdf_path)
            reporter.success(
                f"已验证  {_display_path(pdf_path)} · {page_count} 页"
            )
    except Exception as error:
        reporter.error(error)
        return 1

    reporter.complete(output_path, pdf_path)
    return 0
