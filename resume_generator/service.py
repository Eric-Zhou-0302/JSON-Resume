"""供 Python 调用方使用的稳定简历生成服务。"""

from io import BytesIO
from pathlib import Path
from typing import Any

from .output import prepare_output_target, save_atomically
from .pdf import convert_docx_to_pdf
from .renderer import render_resume
from .validator import load_json, parse_json, parse_locale


def render_json_to_docx(data: dict[str, Any]) -> bytes:
    """校验一份简历 JSON，并在内存中返回完整 DOCX 字节。

    该函数是 CLI 之外的公共集成入口。
    """
    locale = parse_locale(data)
    name, contacts, sections = parse_json(data)
    document = render_resume(
        name,
        contacts,
        sections,
        locale=locale,
    )

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def render_json_file_to_docx(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    pdf: bool = False,
    force: bool = False,
) -> Path:
    """读取 JSON 文件并生成 DOCX，返回生成文件的绝对路径。

    ``output_path`` 省略时，文件写入当前工作目录的 ``output/``。
    ``pdf=True`` 会在同一目录额外生成同名 PDF。该函数使用 Python
    关键字参数，对应 CLI 的 ``-o``、``--pdf`` 和 ``--force``。
    """
    source_path = Path(input_path).expanduser().resolve()
    destination_path = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else Path.cwd() / "output" / source_path.with_suffix(".docx").name
    )
    create_parent = output_path is None
    pdf_path = destination_path.with_suffix(".pdf") if pdf else None

    document_bytes = render_json_to_docx(load_json(source_path))

    prepare_output_target(
        destination_path,
        force=force,
        create_parent=create_parent,
    )
    if pdf_path is not None:
        prepare_output_target(
            pdf_path,
            force=force,
            create_parent=create_parent,
        )

    save_atomically(
        destination_path,
        lambda temporary_path: temporary_path.write_bytes(document_bytes),
        force=force,
        create_parent=create_parent,
    )
    if pdf_path is not None:
        convert_docx_to_pdf(destination_path, pdf_path, force=force)

    return destination_path
