"""可复用的 python-docx 与 OOXML 底层工具。"""

from collections.abc import Iterable
from datetime import datetime, timezone

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.styles.style import _ParagraphStyle
from docx.text.paragraph import Paragraph
from docx.text.run import Run


def clear_core_properties(document: DocumentObject) -> None:
    """写入稳定、无个人信息的文档元数据。"""
    properties = document.core_properties
    for attribute in (
        "author",
        "category",
        "comments",
        "content_status",
        "identifier",
        "keywords",
        "language",
        "last_modified_by",
        "subject",
        "title",
        "version",
    ):
        setattr(properties, attribute, "")
    neutral_timestamp = datetime(2000, 1, 1, tzinfo=timezone.utc)
    properties.created = neutral_timestamp
    properties.modified = neutral_timestamp
    properties.last_printed = neutral_timestamp
    properties.revision = 1


def set_style_fonts(
    style: _ParagraphStyle,
    *,
    en_font: str,
    cn_font: str,
) -> None:
    """显式设置段落样式的西文与东亚字体槽位。"""
    style.font.name = en_font
    run_properties = style.element.get_or_add_rPr()
    run_fonts = run_properties.get_or_add_rFonts()
    run_fonts.set(qn("w:ascii"), en_font)
    run_fonts.set(qn("w:hAnsi"), en_font)
    run_fonts.set(qn("w:eastAsia"), cn_font)


def set_run_fonts(run: Run, *, en_font: str, cn_font: str) -> None:
    """显式设置单个 Run 的西文与东亚字体槽位。"""
    run.font.name = en_font
    run_properties = run._element.get_or_add_rPr()
    run_fonts = run_properties.get_or_add_rFonts()
    run_fonts.set(qn("w:ascii"), en_font)
    run_fonts.set(qn("w:hAnsi"), en_font)
    run_fonts.set(qn("w:eastAsia"), cn_font)


def set_style_numbering(
    style: _ParagraphStyle,
    *,
    num_id: int,
    level: int = 0,
) -> None:
    """把段落样式连接到真实 Word 编号定义。"""
    paragraph_properties = style.element.get_or_add_pPr()
    numbering = paragraph_properties.get_or_add_numPr()
    numbering.get_or_add_ilvl().val = level
    numbering.get_or_add_numId().val = num_id


def set_style_bottom_border(
    style: _ParagraphStyle,
    *,
    color: str,
    size: int = 4,
    space: int = 1,
) -> None:
    """为段落样式设置黑色单线底边框。"""
    paragraph_properties = style.element.get_or_add_pPr()
    borders = paragraph_properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        paragraph_properties.append(borders)

    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color.lstrip("#"))


def add_hyperlink(
    paragraph: Paragraph,
    text: str,
    href: str,
    *,
    en_font: str,
    cn_font: str,
    color: str,
) -> None:
    """添加保持简历黑白样式的外部超链接。"""
    relationship_id = paragraph.part.relate_to(href, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)

    run = OxmlElement("w:r")
    run_properties = OxmlElement("w:rPr")
    run_fonts = OxmlElement("w:rFonts")
    run_fonts.set(qn("w:ascii"), en_font)
    run_fonts.set(qn("w:hAnsi"), en_font)
    run_fonts.set(qn("w:eastAsia"), cn_font)
    run_properties.append(run_fonts)

    run_color = OxmlElement("w:color")
    run_color.set(qn("w:val"), color.lstrip("#"))
    run_properties.append(run_color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "none")
    run_properties.append(underline)
    run.append(run_properties)

    text_element = OxmlElement("w:t")
    text_element.text = text
    run.append(text_element)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def non_empty_text(values: Iterable[str | None], separator: str) -> str:
    """去除两端空白后拼接非空文本字段。"""
    return separator.join(value.strip() for value in values if value and value.strip())
