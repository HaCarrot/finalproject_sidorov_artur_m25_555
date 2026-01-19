from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют."""

    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.

        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код или тикер валюты
        """
        self._validate_name(name)
        self._validate_code(code)

        self._name = name
        self._code = code

    @property
    def name(self) -> str:
        """Геттер для имени валюты."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Сеттер для имени валюты."""
        self._validate_name(value)
        self._name = value

    @property
    def code(self) -> str:
        """Геттер для кода валюты."""
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        """Сеттер для кода валюты."""
        self._validate_code(value)
        self._code = value

    def _validate_name(self, name: str) -> None:
        """Валидация имени валюты."""
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты не может быть пустым")
        if len(name.strip()) == 0:
            raise ValueError("Имя валюты не может содержать только пробелы")

    def _validate_code(self, code: str) -> None:
        """Валидация кода валюты."""
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты не может быть пустым")

        code_clean = code.strip().upper()

        if len(code_clean) < 2 or len(code_clean) > 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")

        if " " in code_clean:
            raise ValueError("Код валюты не может содержать пробелы")

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление для UI/логов.

        Returns:
            Строка с информацией о валюте
        """
        pass


class FiatCurrency(Currency):
    """Класс фиатной валюты."""

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.

        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код валюты
            issuing_country: Страна или зона эмиссии
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Геттер для страны эмиссии."""
        return self._issuing_country

    @issuing_country.setter
    def issuing_country(self, value: str) -> None:
        """Сеттер для страны эмиссии."""
        if not value or not isinstance(value, str):
            raise ValueError("Страна эмиссии не может быть пустой")
        self._issuing_country = value

    def get_display_info(self) -> str:
        """Возвращает строковое представление фиатной валюты."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Класс криптовалюты."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты.

        Args:
            name: Человекочитаемое имя криптовалюты
            code: Тикер криптовалюты
            algorithm: Алгоритм консенсуса/майнинга
            market_cap: Рыночная капитализация
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Геттер для алгоритма."""
        return self._algorithm

    @algorithm.setter
    def algorithm(self, value: str) -> None:
        """Сеттер для алгоритма."""
        if not value or not isinstance(value, str):
            raise ValueError("Алгоритм не может быть пустым")
        self._algorithm = value

    @property
    def market_cap(self) -> float:
        """Геттер для рыночной капитализации."""
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float) -> None:
        """Сеттер для рыночной капитализации."""
        if not isinstance(value, (int, float)):
            raise ValueError("Рыночная капитализация должна быть числом")
        if value < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self._market_cap = float(value)

    def get_display_info(self) -> str:
        """Возвращает строковое представление криптовалюты."""
        if self.market_cap >= 1e12:
            mcap_str = f"{self.market_cap / 1e12:.2f}T"
        elif self.market_cap >= 1e9:
            mcap_str = f"{self.market_cap / 1e9:.2f}B"
        elif self.market_cap >= 1e6:
            mcap_str = f"{self.market_cap / 1e6:.2f}M"
        else:
            mcap_str = f"{self.market_cap:.2f}"

        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})" #noqa: E501


class CurrencyRegistry:
    """Реестр валют с фабричным методом."""

    _currencies: Dict[str, Currency] = {
        "USD": FiatCurrency("US Dollar", "USD", "United States"),
        "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
        "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
        "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
        "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
        "CNY": FiatCurrency("Chinese Yuan", "CNY", "China"),
        "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 450e9),
        "LTC": CryptoCurrency("Litecoin", "LTC", "Scrypt", 6e9),
        "XRP": CryptoCurrency("Ripple", "XRP", "XRP Ledger Consensus", 35e9),
    }

    @classmethod
    def get_currency(cls, code: str) -> Currency:
        """
        Возвращает объект валюты по коду.

        Args:
            code: Код валюты

        Returns:
            Объект Currency

        Raises:
            CurrencyNotFoundError: Если валюта не найдена
        """
        code_upper = code.strip().upper()

        if code_upper not in cls._currencies:
            raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не найдена")

        return cls._currencies[code_upper]

    @classmethod
    def register_currency(cls, currency: Currency) -> None:
        """
        Регистрирует новую валюту в реестре.

        Args:
            currency: Объект валюты для регистрации
        """
        cls._currencies[currency.code] = currency

    @classmethod
    def unregister_currency(cls, code: str) -> None:
        """
        Удаляет валюту из реестра.

        Args:
            code: Код валюты для удаления
        """
        code_upper = code.strip().upper()
        if code_upper in cls._currencies:
            del cls._currencies[code_upper]

    @classmethod
    def get_all_currencies(cls) -> Dict[str, Currency]:
        """
        Возвращает все зарегистрированные валюты.

        Returns:
            Словарь всех валют (код → объект)
        """
        return cls._currencies.copy()

    @classmethod
    def is_currency_registered(cls, code: str) -> bool:
        """
        Проверяет, зарегистрирована ли валюта.

        Args:
            code: Код валюты

        Returns:
            True если валюта зарегистрирована, иначе False
        """
        return code.strip().upper() in cls._currencies


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения валюты по коду.

    Args:
        code: Код валюты

    Returns:
        Объект Currency

    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    return CurrencyRegistry.get_currency(code)
