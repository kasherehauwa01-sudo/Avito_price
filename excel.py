"""Чтение и нормализация XLS/XLSX-файлов с ценами."""

from __future__ import annotations

from difflib import SequenceMatcher
from io import BytesIO
from typing import BinaryIO

import pandas as pd

from config import EXCEL_COLUMNS

# Сколько первых строк файла проверяем при поиске строки заголовков.
HEADER_SEARCH_ROWS = 30

# Минимальная похожесть заголовков для исправления частых опечаток вроде "Артиккул".
HEADER_SIMILARITY_THRESHOLD = 0.82

# Допустимые варианты названий колонок из Excel. Значения приводятся к каноническим
# названиям из EXCEL_COLUMNS, с которыми дальше работает приложение.
HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "Код": ("Код", "Код товара", "Код номенклатуры"),
    "Артикул": ("Артикул", "Артиккул", "Арт.", "Арт", "Артикул товара"),
    "Наименование товаров": (
        "Наименование товаров",
        "Наименование товара",
        "Наименование",
        "Название товара",
        "Товар",
    ),
    "Розничная": ("Розничная", "Розница", "Розничная цена", "Цена розничная"),
}


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


def normalize_header_key(value: object) -> str:
    """Создает ключ заголовка без регистра, пробелов и знаков пунктуации."""
    header = normalize_header(value).casefold()
    return "".join(symbol for symbol in header if symbol.isalnum())


def resolve_header(value: object) -> str | None:
    """Возвращает каноническое имя обязательной колонки по заголовку из Excel."""
    header_key = normalize_header_key(value)
    if not header_key:
        return None

    for canonical_name, aliases in HEADER_ALIASES.items():
        alias_keys = [normalize_header_key(alias) for alias in aliases]
        if header_key in alias_keys:
            return canonical_name

        best_similarity = max(
            SequenceMatcher(None, header_key, alias_key).ratio()
            for alias_key in alias_keys
        )
        if best_similarity >= HEADER_SIMILARITY_THRESHOLD:
            return canonical_name

    return None


def clean_price(value: object) -> str:
    """Возвращает пустую строку для отсутствующей цены или строковое значение цены."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "none", "nan"}:
        return ""
    return text


def get_header_mapping(row_values: list[object]) -> dict[int, str]:
    """Строит соответствие индексов колонок Excel каноническим названиям."""
    mapping: dict[int, str] = {}
    found_canonical_names: set[str] = set()

    for column_index, value in enumerate(row_values):
        canonical_name = resolve_header(value)
        if canonical_name and canonical_name not in found_canonical_names:
            mapping[column_index] = canonical_name
            found_canonical_names.add(canonical_name)

    return mapping


def find_header_row(raw_dataframe: pd.DataFrame) -> tuple[int, dict[int, str]]:
    """Находит индекс строки Excel и колонки, где находятся обязательные заголовки."""
    required_headers = set(EXCEL_COLUMNS)
    rows_to_check = min(len(raw_dataframe), HEADER_SEARCH_ROWS)

    for row_index in range(rows_to_check):
        mapping = get_header_mapping(raw_dataframe.iloc[row_index].tolist())
        if required_headers.issubset(set(mapping.values())):
            return row_index, mapping

    raise ValueError(
        "В Excel не найдена строка заголовков с обязательными колонками: "
        f"{', '.join(EXCEL_COLUMNS)}. Проверьте первые {HEADER_SEARCH_ROWS} строк файла. "
        "Допускаются близкие названия и частые опечатки, например 'Артиккул'."
    )


def build_dataframe_from_detected_header(
    raw_dataframe: pd.DataFrame,
    header_row_index: int,
    header_mapping: dict[int, str],
) -> pd.DataFrame:
    """Создает таблицу данных, используя найденную строку как заголовки колонок."""
    selected_column_indexes = list(header_mapping.keys())
    dataframe = raw_dataframe.iloc[header_row_index + 1 :, selected_column_indexes].copy()
    dataframe.columns = [header_mapping[index] for index in selected_column_indexes]
    dataframe = dataframe.dropna(how="all")
    return dataframe


def read_price_file(uploaded_file: BinaryIO | BytesIO) -> pd.DataFrame:
    """Считывает Excel-файл, автоматически находит заголовки и нормализует данные."""
    raw_dataframe = pd.read_excel(uploaded_file, header=None, engine=None)
    header_row_index, header_mapping = find_header_row(raw_dataframe)
    dataframe = build_dataframe_from_detected_header(
        raw_dataframe,
        header_row_index,
        header_mapping,
    )

    missing_columns = [column for column in EXCEL_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"В Excel отсутствуют обязательные колонки: {', '.join(missing_columns)}")

    result = dataframe.loc[:, EXCEL_COLUMNS].copy()
    result["Артикул"] = result["Артикул"].map(normalize_article)
    result["Розничная"] = result["Розничная"].map(clean_price)
    result = result[result["Артикул"] != ""]
    return result
