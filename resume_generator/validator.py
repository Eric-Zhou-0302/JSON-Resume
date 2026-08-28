"""JSON 输入文件的读取、校验与数据模型转换。"""

from datetime import date
import json
from pathlib import Path
import re
from typing import Any

from .config import SUPPORTED_LOCALES
from .models import Contact, Entry, FieldError, Name, Section

ISO_MONTH_SHAPE = re.compile(r"^\d{4}-\d{2}$")
DATE_LIKE_SHAPE = re.compile(r"^\d{4}-\d{1,2}(?:-\d{1,2})?$")


def _parse_locale_value(value: Any) -> str:
    """校验严格的地区枚举，不做大小写或别名归一化。"""
    if not isinstance(value, str):
        _error("必须为字符串", "locale")
    if value not in SUPPORTED_LOCALES:
        supported = ", ".join(SUPPORTED_LOCALES)
        _error(f"必须为以下值之一: {supported}", "locale")
    return value


def load_json(file_path: str | Path) -> dict[str, Any]:
    """以 UTF-8 读取 JSON 文件，不在此阶段解释字段。"""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"输入文件不存在: {path}")

    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _error(message: str, source: str) -> None:
    """统一抛出带字段路径的校验错误。"""
    raise FieldError(message, source)


def _require_dict(value: Any, source: str) -> dict[str, Any]:
    """确保值为 JSON 对象，而不是 list 或其他类型。"""
    if not isinstance(value, dict):
        _error("必须为对象", source)
    return value


def _require_list(value: Any, source: str) -> list[Any]:
    """确保值为 JSON 数组。"""
    if not isinstance(value, list):
        _error("必须为数组", source)
    return value


def _check_keys(
    value: dict[str, Any],
    required: set[str],
    allowed: set[str],
    source: str,
) -> None:
    """检查对象的必填字段和未知字段。"""
    missing = required - value.keys()
    if missing:
        _error(f"缺少字段: {', '.join(sorted(missing))}", source)

    extra = value.keys() - allowed
    if extra:
        _error(f"存在多余字段: {', '.join(sorted(extra))}", source)


def _parse_month(value: Any, source: str) -> date | None:
    """解析 ``YYYY-MM``，内部以当月第一天保存用于日期比较。"""
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        _error("必须为 YYYY-MM 格式的字符串、空字符串或 null", source)
    if not ISO_MONTH_SHAPE.fullmatch(value):
        _error("必须为有效的 YYYY-MM 日期", source)

    try:
        return date.fromisoformat(f"{value}-01")
    except ValueError:
        _error("必须为有效的 YYYY-MM 日期", source)
        return None


def _parse_end_date(value: Any, source: str) -> date | str | None:
    """解析结束日期。

    ``Entry.end_date`` 允许使用普通字符串表示进行中状态，例如
    ``"至今"`` 或 ``"Present"``；只有 ``YYYY-MM`` 才参与日期先后比较。
    """
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        _error("必须为 YYYY-MM、其他状态字符串、空字符串或 null", source)

    if ISO_MONTH_SHAPE.fullmatch(value):
        return _parse_month(value, source)
    if DATE_LIKE_SHAPE.fullmatch(value):
        _error("必须为有效的 YYYY-MM 日期或状态字符串", source)
    return value


def _parse_contact(contact: Any, index: int) -> Contact:
    source = f"basics.contacts[{index}]"
    contact = _require_dict(contact, source)
    _check_keys(contact, {"label", "href"}, {"label", "href"}, source)

    label = contact["label"]
    href = contact["href"]
    if not isinstance(label, str):
        _error("必须为字符串", f"{source}.label")
    if href is not None and not isinstance(href, str):
        _error("必须为字符串或 null", f"{source}.href")
    if isinstance(href, str) and href.strip() and not label.strip():
        _error("href 非空时 label 不能为空", f"{source}.label")

    return Contact(label=label, href=href)


def _parse_bullets(value: Any, source: str) -> list[str]:
    """解析至少包含一项非空字符串的扁平项目符号数组。"""
    bullets = _require_list(value, source)
    if not bullets:
        _error("至少需要一项", source)
    for index, bullet in enumerate(bullets):
        if not isinstance(bullet, str):
            _error("每一项必须为字符串", f"{source}[{index}]")
        if not bullet.strip():
            _error("不得为空白字符串", f"{source}[{index}]")
    return list(bullets)


def _parse_entry(entry: Any, section_index: int, entry_index: int) -> Entry:
    source = f"sections[{section_index}].entries[{entry_index}]"
    entry = _require_dict(entry, source)
    fields = {"title", "position", "location", "start_date", "end_date", "bullets"}
    _check_keys(entry, set(), fields, source)

    for field in ("title", "position", "location"):
        value = entry.get(field)
        if value is not None and not isinstance(value, str):
            _error("必须为字符串或 null", f"{source}.{field}")

    start_date = _parse_month(entry.get("start_date"), f"{source}.start_date")
    end_date = _parse_end_date(entry.get("end_date"), f"{source}.end_date")
    if start_date and isinstance(end_date, date) and end_date < start_date:
        _error("不能早于 start_date", f"{source}.end_date")

    bullets = (
        _parse_bullets(entry["bullets"], f"{source}.bullets")
        if "bullets" in entry
        else []
    )
    has_text_metadata = any(
        value and value.strip()
        for value in (
            entry.get("title"),
            entry.get("position"),
            entry.get("location"),
        )
    )
    has_date = (
        start_date is not None
        or isinstance(end_date, date)
        or (isinstance(end_date, str) and bool(end_date.strip()))
    )
    if not (has_text_metadata or has_date or bullets):
        _error("至少需要一项非空的元信息或 bullets", source)

    return Entry(
        title=entry.get("title"),
        position=entry.get("position"),
        location=entry.get("location"),
        start_date=start_date,
        end_date=end_date,
        bullets=bullets,
    )


def _parse_section(section: Any, section_index: int) -> Section:
    source = f"sections[{section_index}]"
    section = _require_dict(section, source)
    _check_keys(section, {"title", "entries"}, {"title", "entries"}, source)

    if not isinstance(section["title"], str):
        _error("必须为字符串", f"{source}.title")
    if not section["title"].strip():
        _error("不得为空白字符串", f"{source}.title")

    entries = _require_list(section["entries"], f"{source}.entries")
    if not entries:
        _error("至少需要一项", f"{source}.entries")
    parsed_entries = [
        _parse_entry(entry, section_index, entry_index)
        for entry_index, entry in enumerate(entries)
    ]
    return Section(title=section["title"], entries=parsed_entries)


def parse_json(
    data: dict[str, Any],
) -> tuple[Name, list[Contact], list[Section]]:
    """校验原始字典并转换为现有四类数据模型。

    顶层使用元组返回，避免为 ``Resume`` 或 ``Basics`` 新增包装模型。
    """
    data = _require_dict(data, "root")
    root_fields = {"locale", "basics", "sections"}
    _check_keys(data, root_fields, root_fields, "root")
    _parse_locale_value(data["locale"])

    basics = _require_dict(data["basics"], "basics")
    _check_keys(basics, {"name", "contacts"}, {"name", "contacts"}, "basics")
    name = basics["name"]
    if not isinstance(name, str):
        _error("必须为字符串", "basics.name")

    contacts = _require_list(basics["contacts"], "basics.contacts")
    if not contacts:
        _error("至少存在一个 contact", "basics.contacts")
    parsed_contacts = [
        _parse_contact(contact, index) for index, contact in enumerate(contacts)
    ]

    sections = _require_list(data["sections"], "sections")
    if not sections:
        _error("至少需要一个 section", "sections")
    parsed_sections = [
        _parse_section(section, section_index)
        for section_index, section in enumerate(sections)
    ]

    return Name(name=name), parsed_contacts, parsed_sections


def parse_locale(data: dict[str, Any]) -> str:
    """从严格 JSON 契约中读取页面地区配置。"""
    data = _require_dict(data, "root")
    if "locale" not in data:
        _error("缺少字段: locale", "root")
    return _parse_locale_value(data["locale"])


def validate_json(data: dict[str, Any]) -> None:
    """校验符合严格 JSON 契约的简历数据。

    成功时保持原有接口并返回 ``None``；失败时抛出带完整字段路径的
    ``FieldError``。输入字典不会被修改。
    """
    parse_json(data)
