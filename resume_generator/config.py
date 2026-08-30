"""纸张规格的稳定配置。"""

from typing import Final

A4_PAPER: Final[str] = "A4"
LETTER_PAPER: Final[str] = "Letter"

SUPPORTED_PAPER_SIZES: Final[tuple[str, ...]] = (A4_PAPER, LETTER_PAPER)

PAPER_DIMENSIONS_MM: Final[dict[str, tuple[float, float]]] = {
    A4_PAPER: (210.0, 297.0),
    LETTER_PAPER: (215.9, 279.4),
}
