"""Настройки приложения обновления цен в Google Sheets."""

from __future__ import annotations

from pathlib import Path

# Идентификатор таблицы из URL Google Sheets.
SPREADSHEET_ID: str = "1s7D7d8alvIpQq2rLBGKR6RT2DJKhNPCd5VPjIhDb5Zg"

# GID рабочего листа из URL. По нему приложение найдет нужную вкладку.
WORKSHEET_GID: int = 77890434

# Файл сервисного аккаунта. Для Streamlit Cloud можно использовать secrets.
CREDENTIALS_FILE: Path = Path("credentials.json")

# Первые постоянные колонки таблицы.
FIXED_COLUMNS: tuple[str, str, str] = ("Код", "Артикул", "Наименование товаров")

# Обязательные колонки входного Excel-файла.
EXCEL_COLUMNS: tuple[str, str, str, str] = (
    "Код",
    "Артикул",
    "Наименование товаров",
    "Розничная",
)

# Права доступа, необходимые для чтения/записи таблиц и форматирования ячеек.
GOOGLE_SCOPES: tuple[str, str] = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)

# Цвет подсветки изменившейся цены в формате Google Sheets API.
CHANGED_PRICE_COLOR: dict[str, float] = {"red": 1.0, "green": 0.92, "blue": 0.23}

# Белый фон используется для сброса унаследованной заливки в новой колонке.
DEFAULT_CELL_COLOR: dict[str, float] = {"red": 1.0, "green": 1.0, "blue": 1.0}
