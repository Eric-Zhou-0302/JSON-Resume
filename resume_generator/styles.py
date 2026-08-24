"""简历样式主题与样式管理器。"""

from dataclasses import dataclass

from docx.document import Document as DocumentObject
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.styles.style import _ParagraphStyle, _TableStyle
from docx.table import Table

from .config import A4_PAPER, PAPER_DIMENSIONS_MM
from .helpers import set_style_bottom_border, set_style_fonts, set_style_numbering

NAME_STYLE = "Resume Name"
CONTACT_STYLE = "Resume Contact Information"
SECTION_STYLE = "Resume Section Heading"
ENTRY_TITLE_STYLE = "Resume Entry Heading"
ENTRY_META_STYLE = "Resume Entry Metadata"
BULLET_STYLE = "Resume Bullet"
SUB_BULLET_STYLE = "Resume Sub Bullet"
ENTRY_TABLE_STYLE = "Resume Entry Table"

REQUIRED_PARAGRAPH_STYLES = (
    NAME_STYLE,
    CONTACT_STYLE,
    SECTION_STYLE,
    ENTRY_TITLE_STYLE,
    ENTRY_META_STYLE,
    BULLET_STYLE,
    SUB_BULLET_STYLE,
)

REQUIRED_TABLE_STYLES = (ENTRY_TABLE_STYLE,)


@dataclass(frozen=True)
class ResumeTheme:
    """集中保存可复用的简历视觉参数。"""

    en_font: str = "Times New Roman"
    cn_font: str = "宋体"
    color: str = "#000000"


class ResumeEntryTableStyle:
    """注册并应用项目自有的 60/40 条目表格样式。"""

    column_ratios = (0.6, 0.4)
    cell_margin_twips = 0

    def __init__(self, document: DocumentObject) -> None:
        self.document = document
        self._style: _TableStyle | None = None

    def register(self) -> _TableStyle:
        """幂等注册真实 Word 表格样式及其稳定视觉属性。"""
        try:
            style = self.document.styles[ENTRY_TABLE_STYLE]
        except KeyError:
            style = self.document.styles.add_style(
                ENTRY_TABLE_STYLE,
                WD_STYLE_TYPE.TABLE,
            )
        if style.type != WD_STYLE_TYPE.TABLE:
            raise ValueError(f"项目样式不是表格样式: {ENTRY_TABLE_STYLE}")

        style.base_style = self.document.styles["Normal Table"]
        style.quick_style = True
        style.hidden = False
        self._configure_table_properties(style)
        self._configure_row_properties(style)
        self._configure_cell_properties(style)
        self._style = style
        return style

    def apply(self, table: Table) -> None:
        """应用命名样式，并写入样式无法保存的 60/40 实例几何。"""
        style = self._style or self.register()
        table.style = style

        section = self.document.sections[-1]
        usable_emu = (
            int(section.page_width)
            - int(section.left_margin)
            - int(section.right_margin)
        )
        total_width = round(usable_emu / 635)
        left_width = round(total_width * self.column_ratios[0])
        column_widths = (left_width, total_width - left_width)
        self._set_instance_geometry(table, column_widths, total_width)

    def _configure_table_properties(self, style: _TableStyle) -> None:
        table_properties = _get_or_add_child(style.element, "w:tblPr")

        alignment = _get_or_add_child(table_properties, "w:jc")
        alignment.set(qn("w:val"), "center")

        layout = _get_or_add_child(table_properties, "w:tblLayout")
        layout.set(qn("w:type"), "fixed")

        indent = _get_or_add_child(table_properties, "w:tblInd")
        indent.set(qn("w:type"), "dxa")
        indent.set(qn("w:w"), "0")

        margins = _get_or_add_child(table_properties, "w:tblCellMar")
        for edge in ("top", "left", "bottom", "right"):
            margin = _get_or_add_child(margins, f"w:{edge}")
            margin.set(qn("w:type"), "dxa")
            margin.set(qn("w:w"), str(self.cell_margin_twips))

        borders = _get_or_add_child(table_properties, "w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            border = _get_or_add_child(borders, f"w:{edge}")
            border.set(qn("w:val"), "nil")

    @staticmethod
    def _configure_row_properties(style: _TableStyle) -> None:
        row_properties = _get_or_add_child(style.element, "w:trPr")
        _get_or_add_child(row_properties, "w:cantSplit")

    @staticmethod
    def _configure_cell_properties(style: _TableStyle) -> None:
        cell_properties = _get_or_add_child(style.element, "w:tcPr")
        vertical_alignment = _get_or_add_child(cell_properties, "w:vAlign")
        vertical_alignment.set(qn("w:val"), "center")

    @staticmethod
    def _set_instance_geometry(
        table: Table,
        column_widths: tuple[int, int],
        total_width: int,
    ) -> None:
        if len(table.columns) != len(column_widths):
            raise ValueError("Resume Entry Table 必须恰好包含两列")

        table_properties = table._tbl.tblPr
        table_width = _get_or_add_child(table_properties, "w:tblW")
        table_width.set(qn("w:type"), "dxa")
        table_width.set(qn("w:w"), str(total_width))

        for grid_column, width in zip(
            table._tbl.tblGrid.gridCol_lst,
            column_widths,
            strict=True,
        ):
            grid_column.set(qn("w:w"), str(width))

        for row in table.rows:
            for cell, width in zip(row.cells, column_widths, strict=True):
                cell_width = cell._tc.get_or_add_tcPr().get_or_add_tcW()
                cell_width.set(qn("w:type"), "dxa")
                cell_width.set(qn("w:w"), str(width))


class ResumeStyleManager:
    """持有 Document，并幂等应用页面与项目样式。"""

    def __init__(
        self,
        document: DocumentObject,
        theme: ResumeTheme | None = None,
        *,
        paper_size: str = A4_PAPER,
    ) -> None:
        self.document = document
        self.theme = theme or ResumeTheme()
        if paper_size not in PAPER_DIMENSIONS_MM:
            raise ValueError(f"不支持的纸张规格: {paper_size}")
        self.paper_size = paper_size
        self.entry_table_style = ResumeEntryTableStyle(document)

    def apply(self) -> None:
        """应用页面设置并校验/注册全部项目样式。"""
        self._apply_page_setup()
        self._require_numbering_ids({1, 3})

        self._configure_style(
            NAME_STYLE,
            size=24,
            bold=True,
            alignment=WD_ALIGN_PARAGRAPH.CENTER,
        )
        self._configure_style(
            CONTACT_STYLE,
            size=10.5,
            alignment=WD_ALIGN_PARAGRAPH.CENTER,
        )
        section_style = self._configure_style(
            SECTION_STYLE,
            size=14,
            bold=True,
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
            space_before=6,
            space_after=2,
            keep_with_next=True,
        )
        section_style.font.small_caps = True
        set_style_bottom_border(
            section_style,
            color=self.theme.color,
            size=4,
            space=1,
        )
        self._configure_style(
            ENTRY_TITLE_STYLE,
            size=11,
            bold=True,
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
            space_before=2,
        )
        self._configure_style(
            ENTRY_META_STYLE,
            size=11,
            bold=True,
            alignment=WD_ALIGN_PARAGRAPH.RIGHT,
            space_before=2,
        )
        bullet_style = self._configure_style(BULLET_STYLE, size=11)
        set_style_numbering(bullet_style, num_id=1)
        sub_bullet_style = self._configure_style(SUB_BULLET_STYLE, size=10.5)
        set_style_numbering(sub_bullet_style, num_id=3)

        self.entry_table_style.register()
        self._update_numbering_style_links(
            bullet_style_id=bullet_style.style_id,
            sub_bullet_style_id=sub_bullet_style.style_id,
        )

    def _apply_page_setup(self) -> None:
        page_width_mm, page_height_mm = PAPER_DIMENSIONS_MM[self.paper_size]
        for section in self.document.sections:
            section.orientation = WD_ORIENT.PORTRAIT
            section.page_width = Mm(page_width_mm)
            section.page_height = Mm(page_height_mm)
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

    def _configure_style(
        self,
        name: str,
        *,
        size: float,
        bold: bool = False,
        alignment: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.LEFT,
        space_before: float = 0,
        space_after: float = 0,
        keep_with_next: bool = False,
    ) -> _ParagraphStyle:
        style = self._get_or_add_paragraph_style(name)
        set_style_fonts(style, en_font=self.theme.en_font, cn_font=self.theme.cn_font)
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = RGBColor.from_string(self.theme.color.lstrip("#"))
        style.quick_style = True
        style.hidden = False

        paragraph_format = style.paragraph_format
        paragraph_format.alignment = alignment
        paragraph_format.line_spacing = 1.0
        paragraph_format.space_before = Pt(space_before)
        paragraph_format.space_after = Pt(space_after)
        paragraph_format.keep_with_next = keep_with_next
        return style

    def _get_or_add_paragraph_style(self, name: str) -> _ParagraphStyle:
        try:
            style = self.document.styles[name]
        except KeyError:
            style = self.document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        if style.type != WD_STYLE_TYPE.PARAGRAPH:
            raise ValueError(f"项目样式不是段落样式: {name}")
        return style

    def _update_numbering_style_links(
        self,
        *,
        bullet_style_id: str,
        sub_bullet_style_id: str,
    ) -> None:
        replacements = {
            "Bullet": bullet_style_id,
            "ListBullet": bullet_style_id,
            "SubBullet": sub_bullet_style_id,
            "ListBullet3": sub_bullet_style_id,
        }
        numbering = self.document.part.numbering_part.element
        for paragraph_style in numbering.findall(".//w:pStyle", numbering.nsmap):
            current = paragraph_style.get(qn("w:val"))
            if current in replacements:
                paragraph_style.set(qn("w:val"), replacements[current])

    def _require_numbering_ids(self, required_ids: set[int]) -> None:
        numbering = self.document.part.numbering_part.element
        available_ids = {
            int(element.get(qn("w:numId")))
            for element in numbering.findall(qn("w:num"))
        }
        missing = required_ids - available_ids
        if missing:
            values = ", ".join(str(value) for value in sorted(missing))
            raise ValueError(f"文档缺少 Word 编号定义: {values}")


def _get_or_add_child(parent, tag: str):
    """返回 OOXML 直接子节点，不存在时按需创建。"""
    child = parent.find(qn(tag))
    if child is None:
        child = OxmlElement(tag)
        parent.append(child)
    return child
