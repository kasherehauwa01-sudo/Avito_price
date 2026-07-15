"""Настройка логирования для Streamlit-интерфейса и модулей приложения."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class MemoryLogHandler(logging.Handler):
    """Обработчик, сохраняющий последние сообщения логов в памяти."""

    max_records: int = 2000
    records: Deque[str] = field(default_factory=deque)

    def __post_init__(self) -> None:
        """Инициализирует базовый logging.Handler после создания dataclass."""
        super().__init__()
        self.records = deque(maxlen=self.max_records)

    def emit(self, record: logging.LogRecord) -> None:
        """Добавляет отформатированное сообщение в буфер логов."""
        self.records.append(self.format(record))

    def text(self) -> str:
        """Возвращает все накопленные логи одной строкой."""
        return "\n".join(self.records)


_INTERFACE_HANDLER: MemoryLogHandler | None = None


def setup_logger(name: str = "avito_price") -> tuple[logging.Logger, MemoryLogHandler]:
    """Создает общий логгер приложения и обработчик для окна логов."""
    global _INTERFACE_HANDLER

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")

    if _INTERFACE_HANDLER is None:
        _INTERFACE_HANDLER = MemoryLogHandler()
        _INTERFACE_HANDLER.setFormatter(formatter)

    if _INTERFACE_HANDLER not in logger.handlers:
        logger.addHandler(_INTERFACE_HANDLER)

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger, _INTERFACE_HANDLER
