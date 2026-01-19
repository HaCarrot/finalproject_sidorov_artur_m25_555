import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    """
    Настройка системы логирования приложения.

    Формат: строковый, человекочитаемый
    Ротация: по размеру файла (10 MB) и времени (ежедневно)
    Уровень по умолчанию: INFO
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "actions.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)


setup_logging()
