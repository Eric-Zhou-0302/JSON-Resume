"""在构建前核对手动发布的来源、包版本和 PyPI 状态。"""

import ast
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ReleaseError(RuntimeError):
    """发布前置条件未满足。"""


def validate_source_ref(ref: str) -> None:
    """只接受明确选定的仓库版本标签，不从浮动分支发布。"""
    if not ref.startswith("refs/tags/v") or ref == "refs/tags/v":
        raise ReleaseError(
            "请使用 gh workflow run release.yml --ref <已有的 v* 标签> 发起发布"
        )


def read_package_version(root: Path) -> str:
    """静态读取两处包版本，不执行待发布包的初始化代码。"""
    try:
        with (root / "pyproject.toml").open("rb") as source:
            project = tomllib.load(source).get("project", {})
        module = ast.parse(
            (root / "resume_generator" / "__init__.py").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, SyntaxError) as error:
        raise ReleaseError(f"无法读取包版本: {error}") from error

    if not isinstance(project, dict) or project.get("name") != "json-resume":
        raise ReleaseError("待发布项目名称必须是 json-resume")
    version = project.get("version")
    if not isinstance(version, str) or not version or any(
        character.isspace() for character in version
    ):
        raise ReleaseError("pyproject.toml 必须声明非空且不含空白的包版本")

    runtime_version = None
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in targets
        ):
            try:
                runtime_version = ast.literal_eval(statement.value)
            except (TypeError, ValueError) as error:
                raise ReleaseError("__version__ 必须使用静态字符串声明") from error

    if runtime_version != version:
        raise ReleaseError(
            f"包版本不一致: pyproject.toml={version!r}, "
            f"__version__={runtime_version!r}"
        )
    return version


def ensure_unpublished(version: str) -> None:
    """仅将 PyPI 明确返回的 404 视为未发布，查询失败时停止。"""
    request = Request(
        f"https://pypi.org/pypi/json-resume/{quote(version, safe='')}/json",
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=20):
            pass
    except HTTPError as error:
        if error.code == 404:
            return
        raise ReleaseError(f"PyPI 查询失败，HTTP {error.code}") from error
    except (URLError, OSError) as error:
        raise ReleaseError(f"无法确认 PyPI 版本状态: {error}") from error
    raise ReleaseError(f"json-resume {version} 已在 PyPI 发布，不能重复上传")


def main() -> int:
    """输出通过检查的包版本，以及供人工审批核对的来源摘要。"""
    root = Path(__file__).resolve().parents[2]
    try:
        ref = os.environ.get("GITHUB_REF", "")
        validate_source_ref(ref)
        commit = os.environ.get("GITHUB_SHA", "")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ReleaseError("缺少有效的 GitHub 事件提交号")
        checkout = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if checkout != commit:
            raise ReleaseError("检出的源码与手动发布事件的提交号不一致")

        version = read_package_version(root)
        ensure_unpublished(version)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"package_version={version}\n")
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open(
            "a", encoding="utf-8"
        ) as summary:
            summary.write(
                "## PyPI 发布候选\n\n"
                f"- 来源标签：`{ref}`\n"
                f"- 提交号：`{commit}`\n"
                f"- Python 包：`json-resume=={version}`\n"
            )
    except (ReleaseError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"发布检查失败: {error}", file=sys.stderr)
        return 1

    print(f"发布检查通过: json-resume {version}，来源 {ref} @ {commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
