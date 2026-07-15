"""Вспомогательные функции форматирования диапазонов Google Sheets."""

from __future__ import annotations


def column_index_to_letter(index: int) -> str:
    """Преобразует 1-based индекс колонки в буквенное обозначение A1-нотации."""
    if index < 1:
        raise ValueError("Индекс колонки должен быть больше нуля")

    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters
