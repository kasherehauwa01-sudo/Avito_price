"""Формирование файлов экспорта для загрузки в 1С."""

from __future__ import annotations

from html import escape

XLS_MIME_TYPE = "application/vnd.ms-excel"


def build_articles_xls(articles: list[str]) -> bytes:
    """Создает XLS-совместимый HTML-файл: первая строка пустая, далее артикулы."""
    rows = ["<tr><td></td></tr>"]
    rows.extend(f"<tr><td>{escape(article)}</td></tr>" for article in articles)
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
td {{ mso-number-format:"\\@"; }}
</style>
</head>
<body>
<table>
{''.join(rows)}
</table>
</body>
</html>
"""
    return html.encode("utf-8-sig")
