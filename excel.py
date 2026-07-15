"""Чтение и нормализация XLS/XLSX-файлов с ценами."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import pandas as pd

from config import EXCEL_COLUMNS


def normalize_article(value: object) -> str:
    """Приводит артикул к строке и удаляет пробелы по краям без смены регистра."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_price(value: object) -> str:
    """Возвращает пустую строку для отсутствующей цены или строковое значение цены."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan"}:
        return ""
    return text


def read_price_file(uploaded_file: BinaryIO | BytesIO) -> pd.DataFrame:
    """Считывает Excel-файл, проверяет обязательные колонки и нормализует данные."""
    dataframe = pd.read_excel(uploaded_file, dtype={"Артикул": str}, engine=None)
    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    missing_columns = [column for column in EXCEL_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"В Excel отсутствуют обязательные колонки: {', '.join(missing_columns)}")

    result = dataframe.loc[:, EXCEL_COLUMNS].copy()
    result["Артикул"] = result["Артикул"].map(normalize_article)
    result["Розничная"] = result["Розничная"].map(clean_price)
    result = result[result["Артикул"] != ""]
    return result
