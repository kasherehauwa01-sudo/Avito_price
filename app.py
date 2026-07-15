"""Streamlit-приложение для обновления истории цен в Google Sheets."""

from __future__ import annotations

import time
from datetime import date

import streamlit as st

from excel import read_price_file
from logger import setup_logger
from sheets import ImportStats, import_prices

st.set_page_config(page_title="Обновление цен Google Sheets", page_icon="📊", layout="wide")

README_TEXT = """
## Назначение программы

Приложение автоматизирует обновление истории розничных цен товаров в Google Sheets.
Пользователь загружает XLS/XLSX-файл, выбирает дату, а программа создает новую колонку
с этой датой, переносит цены по артикулам и подсвечивает изменившиеся значения.

## Как пользоваться

1. Скачать Excel с ценами.
2. Открыть приложение.
3. Выбрать файл XLS или XLSX.
4. При необходимости изменить дату.
5. Нажать **Загрузить XLS**.
6. Дождаться окончания обработки и проверить итоговую статистику.

## Как подключить Google Sheets

1. Создать проект в Google Cloud Console.
2. Включить Google Sheets API и Google Drive API.
3. Создать Service Account.
4. Скачать JSON-ключ и переименовать его в `credentials.json`.
5. Положить `credentials.json` рядом с приложением или добавить данные в Streamlit secrets.
6. Открыть Google Таблицу и нажать **Поделиться**.
7. Добавить email сервисного аккаунта как редактора.

## Альтернатива: Google Apps Script

Подробный пример скрипта, публикации веб-приложения и сравнение с Service Account
описаны в `README.md` проекта.
"""


@st.dialog("ReadMe")
def show_readme_dialog() -> None:
    """Показывает подробную справку в модальном окне Streamlit."""
    st.markdown(README_TEXT)


def show_stats(stats: ImportStats, elapsed_seconds: float) -> None:
    """Показывает итоговую статистику импорта в виде карточек Streamlit."""
    st.subheader("Итоговая статистика")
    columns = st.columns(6)
    columns[0].metric("Обработано товаров", stats.processed)
    columns[1].metric("Найдено", stats.found)
    columns[2].metric("Добавлено", stats.added)
    columns[3].metric("Изменено цен", stats.changed)
    columns[4].metric("Без изменений", stats.unchanged)
    columns[5].metric("Ошибок", stats.errors)
    st.info(f"Время выполнения: {elapsed_seconds:.0f} секунд")


def main() -> None:
    """Запускает пользовательский интерфейс Streamlit."""
    logger, memory_handler = setup_logger()

    st.title("Обновление цен Google Sheets")
    st.caption("Загрузка XLS/XLSX, создание новой колонки с датой и подсветка изменившихся цен.")

    with st.sidebar:
        st.header("Параметры импорта")
        uploaded_file = st.file_uploader("Выберите XLS/XLSX файл", type=("xls", "xlsx"))
        selected_date = st.date_input("Дата новой колонки", value=date.today(), format="DD.MM.YYYY")
        readme_clicked = st.button("ReadMe", use_container_width=True)

    if readme_clicked:
        show_readme_dialog()

    progress_bar = st.progress(0, text="Ожидание запуска импорта")
    log_box = st.empty()

    if st.button("Загрузить XLS", type="primary", disabled=uploaded_file is None):
        start_time = time.perf_counter()
        try:
            logger.info("Чтение Excel-файла...")
            excel_data = read_price_file(uploaded_file)
            logger.info("Excel-файл успешно прочитан.")

            def update_progress(value: float) -> None:
                """Обновляет progress bar и окно логов во время обработки."""
                percent = int(value * 100)
                progress_bar.progress(percent, text=f"Выполнено {percent}%")
                log_box.text_area("Логи", memory_handler.text(), height=420)

            stats = import_prices(excel_data, selected_date, logger, update_progress)
            progress_bar.progress(100, text="Импорт завершен")
            elapsed_seconds = time.perf_counter() - start_time
            show_stats(stats, elapsed_seconds)
            st.success("Импорт успешно завершен.")
        except Exception as exc:  # noqa: BLE001 - все ошибки должны попасть в интерфейс.
            logger.exception("Критическая ошибка импорта: %s", exc)
            st.error(str(exc))
        finally:
            log_box.text_area("Логи", memory_handler.text(), height=420)
    else:
        log_box.text_area("Логи", memory_handler.text(), height=420)


if __name__ == "__main__":
    main()
