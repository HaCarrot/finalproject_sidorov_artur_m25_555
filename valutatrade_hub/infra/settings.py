import json
import os
from typing import Any, Dict, Optional


class SingletonMeta(type):
    """
    Метакласс для реализации паттерна Singleton.

    Выбран способ через метакласс, так как:
    1. Позволяет контролировать создание экземпляра на уровне метапрограммирования
    2. Читаем и понятен для других разработчиков
    3. Позволяет легко расширять функциональность в будущем
    4. Избегает проблем с многопоточностью при импортах
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Контролирует создание экземпляра класса."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SettingsLoader(metaclass=SingletonMeta):
    """
    Singleton для загрузки и управления настройками приложения.

    Гарантирует существование только одного экземпляра в приложении.
    """

    DATA_DIR = "data_dir"
    USERS_FILE = "users_file"
    PORTFOLIOS_FILE = "portfolios_file"
    RATES_FILE = "rates_file"
    RATES_TTL_SECONDS = "rates_ttl_seconds"
    DEFAULT_BASE_CURRENCY = "default_base_currency"
    LOG_FORMAT = "log_format"
    LOG_LEVEL = "log_level"

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Инициализация загрузчика настроек."""
        self._config: Dict[str, Any] = {}
        self._config_path = config_path

        self._default_config = {
            self.DATA_DIR: "data",
            self.USERS_FILE: "users.json",
            self.PORTFOLIOS_FILE: "portfolios.json",
            self.RATES_FILE: "rates.json",
            self.RATES_TTL_SECONDS: 300,  # 5 минут
            self.DEFAULT_BASE_CURRENCY: "USD",
            self.LOG_FORMAT: "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            self.LOG_LEVEL: "INFO",
        }

        self.reload()

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла или использует значения по умолчанию."""
        self._config = self._default_config.copy()

        if self._config_path and os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    external_config = json.load(f)
                    self._config.update(external_config)
            except (json.JSONDecodeError, IOError) as e:
                # В продакшене здесь должно быть логирование
                print(f"Warning: Failed to load config from {self._config_path}: {e}")

        # Обновляем пути файлов с учетом data_dir
        data_dir = self._config.get(self.DATA_DIR, "data")
        self._config[self.USERS_FILE] = os.path.join(data_dir, "users.json")
        self._config[self.PORTFOLIOS_FILE] = os.path.join(data_dir, "portfolios.json")
        self._config[self.RATES_FILE] = os.path.join(data_dir, "rates.json")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение настройки по ключу.

        Args:
            key: Ключ настройки
            default: Значение по умолчанию если ключ не найден

        Returns:
            Значение настройки или default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Устанавливает значение настройки.

        Args:
            key: Ключ настройки
            value: Значение настройки
        """
        self._config[key] = value

    def get_data_dir(self) -> str:
        """Получает путь к директории с данными."""
        return self.get(self.DATA_DIR, "data")

    def get_users_file(self) -> str:
        """Получает путь к файлу пользователей."""
        return self.get(self.USERS_FILE)

    def get_portfolios_file(self) -> str:
        """Получает путь к файлу портфелей."""
        return self.get(self.PORTFOLIOS_FILE)

    def get_rates_file(self) -> str:
        """Получает путь к файлу курсов."""
        return self.get(self.RATES_FILE)

    def get_rates_ttl(self) -> int:
        """Получает TTL для кэширования курсов в секундах."""
        return self.get(self.RATES_TTL_SECONDS, 300)

    def get_default_base_currency(self) -> str:
        """Получает валюту по умолчанию для отображения."""
        return self.get(self.DEFAULT_BASE_CURRENCY, "USD")

    def get_log_format(self) -> str:
        """Получает формат логов."""
        return self.get(self.LOG_FORMAT)

    def get_log_level(self) -> str:
        """Получает уровень логирования."""
        return self.get(self.LOG_LEVEL)


# Создаем глобальный экземпляр синглтона
settings = SettingsLoader()
