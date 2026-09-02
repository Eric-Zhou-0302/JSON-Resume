"""发布前置检查：仓库标签与包版本解耦，并阻止重复或未经确认的上传。"""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / ".github" / "scripts" / "check_release.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("check_release", SCRIPT_PATH)
if SCRIPT_SPEC is None or SCRIPT_SPEC.loader is None:
    raise RuntimeError("无法加载发布检查脚本")
check_release = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(check_release)


class TestReleaseSource(unittest.TestCase):
    """包发布必须指向已经选择的仓库发布标签。"""

    def test_release_tag_is_accepted(self) -> None:
        check_release.validate_source_ref("refs/tags/v1.1.4")

    def test_branch_or_missing_release_tag_is_rejected(self) -> None:
        for source_ref in (
            "",
            "refs/heads/main",
            "refs/heads/v1.1.4",
            "refs/tags/v",
            "refs/tags/1.1.4",
            "v1.1.4",
        ):
            with self.subTest(source_ref=source_ref):
                with self.assertRaises(check_release.ReleaseError):
                    check_release.validate_source_ref(source_ref)


class TestReleasePackageVersion(unittest.TestCase):
    """从源码静态读取版本，避免发布检查执行包的导入逻辑。"""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.metadata_path = self.root / "pyproject.toml"
        self.package_path = self.root / "resume_generator" / "__init__.py"
        self.package_path.parent.mkdir()
        self.metadata_path.write_text(
            '[project]\nname = "json-resume"\nversion = "1.1.3"\n',
            encoding="utf-8",
        )
        self.package_path.write_text('__version__ = "1.1.3"\n', encoding="utf-8")

    def test_repository_tag_can_differ_from_package_version(self) -> None:
        # 仓库可以因 Skill 更新先行发布，包仍使用自己的版本序列。
        check_release.validate_source_ref("refs/tags/v1.2.0")
        self.assertEqual(check_release.read_package_version(self.root), "1.1.3")

    def test_version_read_does_not_execute_package_code(self) -> None:
        self.package_path.write_text(
            '__version__ = "1.1.3"\nraise RuntimeError("禁止执行包代码")\n',
            encoding="utf-8",
        )
        self.assertEqual(check_release.read_package_version(self.root), "1.1.3")

    def test_mismatched_runtime_version_is_rejected(self) -> None:
        self.package_path.write_text('__version__ = "1.1.2"\n', encoding="utf-8")
        with self.assertRaises(check_release.ReleaseError):
            check_release.read_package_version(self.root)

    def test_nonstatic_or_missing_runtime_version_is_rejected(self) -> None:
        for package_source in (
            '__version__ = ".".join(["1", "1", "3"])\n',
            '__version__ = VERSION\n',
            "__version__ = 113\n",
            "__version__ = None\n",
            'OTHER_VALUE = "1.1.3"\n',
        ):
            with self.subTest(package_source=package_source):
                self.package_path.write_text(package_source, encoding="utf-8")
                with self.assertRaises(check_release.ReleaseError):
                    check_release.read_package_version(self.root)

    def test_wrong_package_name_is_rejected(self) -> None:
        self.metadata_path.write_text(
            '[project]\nname = "example-package"\nversion = "1.1.3"\n',
            encoding="utf-8",
        )
        with self.assertRaises(check_release.ReleaseError):
            check_release.read_package_version(self.root)

    def test_missing_or_nonstring_metadata_version_is_rejected(self) -> None:
        for metadata in (
            '[project]\nname = "json-resume"\n',
            '[project]\nname = "json-resume"\nversion = 113\n',
            '[project]\nname = "json-resume"\nversion = ""\n',
        ):
            with self.subTest(metadata=metadata):
                self.metadata_path.write_text(metadata, encoding="utf-8")
                with self.assertRaises(check_release.ReleaseError):
                    check_release.read_package_version(self.root)

    def test_missing_project_files_are_rejected(self) -> None:
        for file_path in (self.metadata_path, self.package_path):
            with self.subTest(file_path=file_path.name):
                original = file_path.read_text(encoding="utf-8")
                file_path.unlink()
                try:
                    with self.assertRaises(check_release.ReleaseError):
                        check_release.read_package_version(self.root)
                finally:
                    file_path.write_text(original, encoding="utf-8")

    def test_invalid_project_metadata_is_rejected(self) -> None:
        self.metadata_path.write_text("[project\n", encoding="utf-8")
        with self.assertRaises(check_release.ReleaseError):
            check_release.read_package_version(self.root)


class TestReleasePublicationCheck(unittest.TestCase):
    """仅 PyPI 明确返回 404 才允许继续发布；网络故障必须中止。"""

    version = "1.1.3"
    url = "https://pypi.org/pypi/json-resume/1.1.3/json"

    def test_existing_pypi_version_is_rejected(self) -> None:
        response = MagicMock()
        response.status = 200
        response.getcode.return_value = 200
        response.__enter__.return_value = response
        with patch.object(check_release, "urlopen", return_value=response):
            with self.assertRaises(check_release.ReleaseError):
                check_release.ensure_unpublished(self.version)

    def test_pypi_not_found_allows_release(self) -> None:
        not_found = HTTPError(self.url, 404, "Not Found", None, None)
        with patch.object(check_release, "urlopen", side_effect=not_found) as request:
            check_release.ensure_unpublished(self.version)
        request.assert_called_once()

    def test_other_http_errors_stop_release(self) -> None:
        for status in (401, 403, 429, 500, 503):
            with self.subTest(status=status):
                error = HTTPError(self.url, status, "Request failed", None, None)
                with patch.object(check_release, "urlopen", side_effect=error):
                    with self.assertRaises(check_release.ReleaseError):
                        check_release.ensure_unpublished(self.version)

    def test_network_failure_stops_release(self) -> None:
        with patch.object(
            check_release,
            "urlopen",
            side_effect=URLError("Network unavailable"),
        ):
            with self.assertRaises(check_release.ReleaseError):
                check_release.ensure_unpublished(self.version)

    def test_timeout_stops_release(self) -> None:
        with patch.object(
            check_release,
            "urlopen",
            side_effect=TimeoutError("Request timed out"),
        ):
            with self.assertRaises(check_release.ReleaseError):
                check_release.ensure_unpublished(self.version)


class TestReleaseMain(unittest.TestCase):
    """验证失败会停止输出发布候选，成功摘要保留可核对的来源信息。"""

    commit = "a" * 40
    version_url = "https://pypi.org/pypi/json-resume/1.1.3/json"

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "json-resume"\nversion = "1.1.3"\n',
            encoding="utf-8",
        )
        package_path = self.root / "resume_generator" / "__init__.py"
        package_path.parent.mkdir()
        package_path.write_text('__version__ = "1.1.3"\n', encoding="utf-8")
        self.output_path = self.root / "github-output.txt"
        self.summary_path = self.root / "github-summary.md"
        self.output_path.write_text("existing=value\n", encoding="utf-8")
        self.summary_path.write_text("Existing summary\n", encoding="utf-8")

        environment = patch.dict(
            check_release.os.environ,
            {
                "GITHUB_REF": "refs/tags/v1.2.0",
                "GITHUB_SHA": self.commit,
                "GITHUB_OUTPUT": str(self.output_path),
                "GITHUB_STEP_SUMMARY": str(self.summary_path),
            },
            clear=True,
        )
        environment.start()
        self.addCleanup(environment.stop)
        script_path = patch.object(
            check_release,
            "__file__",
            str(self.root / ".github" / "scripts" / "check_release.py"),
        )
        script_path.start()
        self.addCleanup(script_path.stop)
        git_command = patch.object(
            check_release.subprocess,
            "run",
            return_value=MagicMock(stdout=f"{self.commit}\n"),
        )
        self.git_command = git_command.start()
        self.addCleanup(git_command.stop)
        request = patch.object(
            check_release,
            "urlopen",
            side_effect=HTTPError(self.version_url, 404, "Not Found", None, None),
        )
        self.request = request.start()
        self.addCleanup(request.stop)

    def run_main(self) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = check_release.main()
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def assert_candidate_output_unchanged(self) -> None:
        self.assertEqual(
            self.output_path.read_text(encoding="utf-8"),
            "existing=value\n",
        )
        self.assertEqual(
            self.summary_path.read_text(encoding="utf-8"),
            "Existing summary\n",
        )

    def test_valid_candidate_outputs_independent_package_version(self) -> None:
        exit_code, stdout, stderr = self.run_main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("1.1.3", stdout)
        self.assertEqual(
            self.output_path.read_text(encoding="utf-8"),
            "existing=value\npackage_version=1.1.3\n",
        )
        summary = self.summary_path.read_text(encoding="utf-8")
        for source_detail in ("refs/tags/v1.2.0", self.commit, "json-resume==1.1.3"):
            self.assertIn(source_detail, summary)

    def test_invalid_event_does_not_output_candidate(self) -> None:
        for environment in (
            {"GITHUB_REF": "refs/heads/main"},
            {"GITHUB_SHA": ""},
        ):
            with self.subTest(environment=environment):
                with patch.dict(check_release.os.environ, environment):
                    exit_code, stdout, stderr = self.run_main()
                self.assertEqual(exit_code, 1)
                self.assertEqual(stdout, "")
                self.assertTrue(stderr)
                self.assert_candidate_output_unchanged()
        self.request.assert_not_called()

    def test_checkout_mismatch_does_not_output_candidate(self) -> None:
        self.git_command.return_value.stdout = f'{"b" * 40}\n'
        exit_code, stdout, stderr = self.run_main()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr)
        self.assert_candidate_output_unchanged()
        self.request.assert_not_called()

    def test_pypi_failure_does_not_output_candidate(self) -> None:
        self.request.side_effect = HTTPError(
            self.version_url, 503, "Service unavailable", None, None
        )
        exit_code, stdout, stderr = self.run_main()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr)
        self.assert_candidate_output_unchanged()


if __name__ == "__main__":
    unittest.main()
