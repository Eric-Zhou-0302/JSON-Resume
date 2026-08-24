"""输入地区与页面规格的稳定配置。"""

from typing import Final

A4_PAPER: Final[str] = "a4"
LETTER_PAPER: Final[str] = "letter"

SUPPORTED_LOCALES: Final[tuple[str, ...]] = (
    "zh-CN",
    "en-US",
    "en-GB",
    "en-EU",
)

LOCALE_PAPER_SIZE: Final[dict[str, str]] = {
    "zh-CN": A4_PAPER,
    "en-US": LETTER_PAPER,
    "en-GB": A4_PAPER,
    "en-EU": A4_PAPER,
}

PAPER_DIMENSIONS_MM: Final[dict[str, tuple[float, float]]] = {
    A4_PAPER: (210.0, 297.0),
    LETTER_PAPER: (215.9, 279.4),
}


def paper_size_for_locale(locale: str) -> str:
    """返回地区对应的纸张规格，并拒绝未支持的地区。"""
    try:
        return LOCALE_PAPER_SIZE[locale]
    except KeyError as error:
        supported = ", ".join(SUPPORTED_LOCALES)
        raise ValueError(f"不支持的 locale: {locale}；可选值: {supported}") from error
