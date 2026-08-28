"""简历生成器使用的纯数据模型。"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Name:
    """简历顶部显示的姓名。"""

    name: str


@dataclass
class Contact:
    """一项联系方式。

    ``label`` 是文档中可见的文字，``href`` 仅作为可选超链接目标。
    """

    label: str
    href: str | None = None


@dataclass
class Entry:
    """一个教育、经历、项目或技能条目。"""

    bullets: list[str] = field(default_factory=list)
    title: str | None = None
    position: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | str | None = None


@dataclass
class Section:
    """一组按顺序渲染的简历条目。"""

    title: str
    entries: list[Entry]


@dataclass
class FieldError(Exception):
    """带 JSON 字段路径的输入错误。"""

    message: str
    source: str | None = None

    def __post_init__(self) -> None:
        if self.source:
            super().__init__(f"{self.source}: {self.message}")
        else:
            super().__init__(self.message)
