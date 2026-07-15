"""Чтение и нормализация XLS/XLSX-файлов с ценами."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import pandas as pd

from config import EXCEL_COLUMNS

# Сколько первых строк файла проверяем при поиске строки заголовков.
HEADER_SEARCH_ROWS = 30


def normalize_article(value: object) -> str:
    """Приводит артикул к строке и удаляет пробелы по краям без смены регистра."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_header(value: object) -> str:
    """Нормализует заголовок Excel для надежного поиска обязательных колонок."""
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()


def clean_price(value: object) -> str:
    """Возвращает пустую строку для отсутствующей цены или строковое значение цены."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan"}:
        return ""
    return text


def find_header_row(raw_dataframe: pd.DataFrame) -> int:
    """Находит индекс строки Excel, в которой находятся обязательные заголовки."""
    required_headers = {normalize_header(column) for column in EXCEL_COLUMNS}
    rows_to_check = min(len(raw_dataframe), HEADER_SEARCH_ROWS)

    for row_index in range(rows_to_check):
        row_headers = {
            normalize_header(value)
            for value in raw_dataframe.iloc[row_index].tolist()
        }
        if required_headers.issubset(row_headers):
            return row_index

    raise ValueError(
        "В Excel не найдена строка заголовков с обязательными колонками: "
        f"{', '.join(EXCEL_COLUMNS)}. Проверьте первые {HEADER_SEARCH_ROWS} строк файла."
    )


def build_dataframe_from_detected_header(
    raw_dataframe: pd.DataFrame,
    header_row_index: int,
) -> pd.DataFrame:
    """Создает таблицу данных, используя найденную строку как заголовки колонок."""
    headers = [
        normalize_header(value)
        for value in raw_dataframe.iloc[header_row_index].tolist()
    ]
    dataframe = raw_dataframe.iloc[header_row_index + 1 :].copy()
    dataframe.columns = headers
    dataframe = dataframe.dropna(how="all")
    dataframe = dataframe.loc[:, [column for column in dataframe.columns if column != ""]]
    return dataframe


def read_price_file(uploaded_file: BinaryIO | BytesIO) -> pd.DataFrame:
    """Считывает Excel-файл, автоматически находит заголовки и нормализует данные."""
    raw_dataframe = pd.read_excel(uploaded_file, header=None, engine=None)
    header_row_index = find_header_row(raw_dataframe)
    dataframe = build_dataframe_from_detected_header(raw_dataframe, header_row_index)

    missing_columns = [column for column in EXCEL_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"В Excel отсутствуют обязательные колонки: {', '.join(missing_columns)}")

    result = dataframe.loc[:, EXCEL_COLUMNS].copy()
    result["Артикул"] = result["Артикул"].map(normalize_article)
    result["Розничная"] = result["Розничная"].map(clean_price)
    result = result[result["Артикул"] != ""]
    return result
