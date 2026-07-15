"""Работа с Google Sheets: чтение, обновление цен и форматирование."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gspread import Worksheet

from config import (
    CHANGED_PRICE_COLOR,
    DEFAULT_CELL_COLOR,
    CREDENTIALS_FILE,
    FIXED_COLUMNS,
    GOOGLE_SCOPES,
    SPREADSHEET_ID,
    WORKSHEET_GID,
)
from excel import clean_price, normalize_article
from formatter import column_index_to_letter

ProgressCallback = Callable[[float], None]


@dataclass
class ImportStats:
    """Итоговая статистика импорта цен."""

    processed: int = 0
    found: int = 0
    added: int = 0
    changed: int = 0
    unchanged: int = 0
    errors: int = 0


def _load_credentials(credentials_path: Path = CREDENTIALS_FILE) -> Credentials:
    """Загружает credentials из Streamlit secrets или локального credentials.json."""
    if "gcp_service_account" in st.secrets:
        credentials_info = dict(st.secrets["gcp_service_account"])
        return Credentials.from_service_account_info(credentials_info, scopes=GOOGLE_SCOPES)

    if credentials_path.exists():
        return Credentials.from_service_account_file(credentials_path, scopes=GOOGLE_SCOPES)

    raise FileNotFoundError(
        "Не найден credentials.json и не заполнен st.secrets['gcp_service_account']. "
        "Добавьте учетные данные сервисного аккаунта."
    )


def connect_to_google(logger: logging.Logger) -> tuple[gspread.Client, Worksheet, Any]:
    """Подключается к Google Sheets и возвращает клиент, лист и сервис API."""
    logger.info("Подключение к Google Sheets...")
    credentials = _load_credentials()
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = next(
        sheet for sheet in spreadsheet.worksheets() if sheet.id == WORKSHEET_GID
    )
    sheets_service = build("sheets", "v4", credentials=credentials)
    logger.info("Google авторизация выполнена. Открыт лист: %s", worksheet.title)
    return client, worksheet, sheets_service


def _find_last_date_column(headers: list[str]) -> int:
    """Возвращает 1-based индекс последней колонки с датой после постоянных колонок."""
    if len(headers) <= len(FIXED_COLUMNS):
        return len(FIXED_COLUMNS)
    return len(headers)


def _format_header_and_changes(
    sheets_service: Any,
    sheet_id: int,
    new_column_index: int,
    changed_rows: list[int],
    total_rows: int,
) -> None:
    """Форматирует заголовок новой колонки и подсвечивает измененные цены."""
    requests: list[dict[str, Any]] = []

    if total_rows > 1:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": total_rows,
                        "startColumnIndex": new_column_index - 1,
                        "endColumnIndex": new_column_index,
                    },
                    "cell": {"userEnteredFormat": {"backgroundColor": DEFAULT_CELL_COLOR}},
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
        )

    requests.append(
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": new_column_index - 1,
                    "endColumnIndex": new_column_index,
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True},
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,textFormat)",
            }
        }
    )

    for row_number in changed_rows:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_number - 1,
                        "endRowIndex": row_number,
                        "startColumnIndex": new_column_index - 1,
                        "endColumnIndex": new_column_index,
                    },
                    "cell": {"userEnteredFormat": {"backgroundColor": CHANGED_PRICE_COLOR}},
                    "fields": "userEnteredFormat.backgroundColor",
                }
            }
        )

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": requests},
    ).execute()


def import_prices(
    excel_data: pd.DataFrame,
    selected_date: date,
    logger: logging.Logger,
    progress_callback: ProgressCallback | None = None,
) -> ImportStats:
    """Импортирует цены из Excel в новую колонку Google Sheets."""
    stats = ImportStats()
    _, worksheet, sheets_service = connect_to_google(logger)

    values = worksheet.get_all_values()
    if not values:
        raise ValueError("Google таблица пуста: отсутствует строка заголовков.")

    headers = values[0]
    logger.info("Получено строк: %s", max(len(values) - 1, 0))
    logger.info("Получено товаров из Excel: %s", len(excel_data))

    last_date_column = _find_last_date_column(headers)
    new_column_index = last_date_column + 1
    new_column_letter = column_index_to_letter(new_column_index)
    previous_column_index = last_date_column

    logger.info("Создание новой колонки %s...", new_column_letter)
    worksheet.update(
        range_name=f"{new_column_letter}1",
        values=[[selected_date.strftime("%d.%m.%Y")]],
        value_input_option="RAW",
    )

    article_to_row: dict[str, int] = {}
    for row_number, row in enumerate(values[1:], start=2):
        article = normalize_article(row[1] if len(row) > 1 else "")
        if article:
            article_to_row[article] = row_number

    updates: list[dict[str, Any]] = []
    rows_to_append: list[list[Any]] = []
    changed_rows: list[int] = []
    total = max(len(excel_data), 1)

    for index, row in excel_data.iterrows():
        try:
            article = normalize_article(row["Артикул"])
            price = clean_price(row["Розничная"])
            stats.processed += 1
            logger.info("Поиск артикула %s...", article)

            if article in article_to_row:
                row_number = article_to_row[article]
                stats.found += 1
                logger.info("Найден.")
                updates.append({"range": f"{new_column_letter}{row_number}", "values": [[price]]})

                previous_price = ""
                if row_number <= len(values):
                    source_row = values[row_number - 1]
                    if len(source_row) >= previous_column_index:
                        previous_price = clean_price(source_row[previous_column_index - 1])

                if price != "" and price != previous_price:
                    stats.changed += 1
                    changed_rows.append(row_number)
                    logger.info("Цена изменена. Ячейка подсвечена.")
                else:
                    stats.unchanged += 1
                    logger.info("Без изменений.")
            else:
                new_row_number = len(values) + len(rows_to_append) + 1
                stats.added += 1
                base_row = [row["Код"], article, row["Наименование товаров"]]
                padded_row = base_row + [""] * (new_column_index - len(base_row) - 1) + [price]
                rows_to_append.append(padded_row)
                if price != "":
                    changed_rows.append(new_row_number)
                    stats.changed += 1
                logger.info("Добавлена новая строка.")
        except Exception as exc:  # noqa: BLE001 - ошибка строки не должна останавливать импорт.
            stats.errors += 1
            logger.exception("Ошибка обработки строки Excel %s: %s", index + 2, exc)
        finally:
            if progress_callback:
                progress_callback(stats.processed / total)

    if rows_to_append:
        worksheet.append_rows(rows_to_append, value_input_option="RAW")

    if updates:
        worksheet.batch_update(updates, value_input_option="RAW")

    total_rows = len(values) + len(rows_to_append)
    _format_header_and_changes(
        sheets_service,
        worksheet.id,
        new_column_index,
        changed_rows,
        total_rows,
    )
    logger.info("Импорт завершен.")
    return stats
