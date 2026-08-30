"""Python 包元数据与公共入口的回归测试。"""

from pathlib import Path
import tomllib
import unittest

import resume_generator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestPackageMetadata(unittest.TestCase):
    """防止发布版本和安装命令入口与运行时代码漂移。"""

    @classmethod
    def setUpClass(cls) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as project_file:
            cls.metadata = tomllib.load(project_file)

    def test_distribution_version_matches_runtime_version(self) -> None:
        self.assertEqual(
            self.metadata["project"]["version"],
            resume_generator.__version__,
        )

    def test_distribution_name_is_public_package_name(self) -> None:
        self.assertEqual(
            self.metadata["project"]["name"],
            "json-resume",
        )

    def test_console_script_targets_cli_main(self) -> None:
        self.assertEqual(
            self.metadata["project"]["scripts"]["json-resume"],
            "resume_generator.cli:main",
        )

    def test_all_runtime_dependencies_are_installed_together(self) -> None:
        self.assertEqual(
            self.metadata["project"]["dependencies"],
            [
                "python-docx==1.2.0",
                "docx2pdf==0.1.8",
                "pypdf==6.10.0",
            ],
        )
        self.assertNotIn("optional-dependencies", self.metadata["project"])


if __name__ == "__main__":
    unittest.main()
