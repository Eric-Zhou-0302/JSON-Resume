"""DOCX 输出目标检查与原子写入。"""

from collections.abc import Callable
import os
from pathlib import Path
import tempfile


def prepare_output_target(
    output_path: Path,
    *,
    force: bool,
    create_parent: bool = False,
) -> None:
    """检查输出目录和覆盖条件，不写入任何文件。"""
    parent = output_path.parent
    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)
    if not parent.is_dir():
        raise NotADirectoryError(f"输出目录不存在: {parent}")
    if output_path.exists() and not force:
        raise FileExistsError(
            f"输出文件已存在；如需覆盖请使用 --force: {output_path}"
        )


def save_atomically(
    output_path: Path,
    write_temporary_file: Callable[[Path], None],
    *,
    force: bool,
    create_parent: bool = False,
) -> None:
    """通过同目录临时文件原子写入，避免留下半份 DOCX。"""
    prepare_output_target(
        output_path,
        force=force,
        create_parent=create_parent,
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}.",
        suffix=".docx",
        dir=output_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        write_temporary_file(temporary_path)
        if output_path.exists() and not force:
            raise FileExistsError(
                f"输出文件已存在；如需覆盖请使用 --force: {output_path}"
            )
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
