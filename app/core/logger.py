import os
import sys
import logging

from logging.handlers import RotatingFileHandler


def setup_logger():
    """Настройка централизованного логгера"""
    logger = logging.getLogger("performance_review")
    logger.setLevel(logging.INFO)

    # Очищаем существующие handlers (на случай переинициализации)
    logger.handlers.clear()

    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольный handler - ВСЕГДА РАБОТАЕТ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (ротация логов)
    log_dir = "logs"
    log_file = os.path.join(log_dir, "performance_review.log")

    try:
        # Создаем директорию если не существует
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"Создана директория логов: {log_dir}")

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)  # В файл пишем больше информации
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info("Файловый handler для логов успешно создан: %s", log_file)

    except Exception as e:
        logger.warning("Не удалось создать файловый handler: %s", e)
        logger.info("Логи будут выводиться только в консоль")

    logger.info("Логгер инициализирован. Вывод в консоль и файл %s", log_file)
    return logger


# Создаем глобальный логгер
logger = setup_logger()
