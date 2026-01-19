import hashlib
from datetime import datetime
from typing import Dict, Optional


class User:
    """Класс пользователя системы."""
    
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime
    ):
        """
        Инициализация пользователя.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            hashed_password: Хешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username  
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date
    
    @property
    def user_id(self) -> int:
        """Геттер для ID пользователя."""
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: int) -> None:
        """Сеттер для ID пользователя."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError("ID пользователя должен быть положительным целым числом")
        self._user_id = value
    
    @property
    def username(self) -> str:
        """Геттер для имени пользователя."""
        return self._username
    
    @username.setter
    def username(self, value: str) -> None:
        """Сеттер для имени пользователя."""
        if not value or not isinstance(value, str):
            raise ValueError("Имя пользователя не может быть пустым")
        if len(value.strip()) == 0:
            raise ValueError("Имя пользователя не может содержать только пробелы")
        self._username = value.strip()
    
    @property
    def hashed_password(self) -> str:
        """Геттер для хешированного пароля."""
        return self._hashed_password
    
    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        """Сеттер для хешированного пароля."""
        if not value or not isinstance(value, str):
            raise ValueError("Пароль не может быть пустым")
        if len(value) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        self._hashed_password = value
    
    @property
    def salt(self) -> str:
        """Геттер для соли."""
        return self._salt
    
    @salt.setter
    def salt(self, value: str) -> None:
        """Сеттер для соли."""
        if not value or not isinstance(value, str):
            raise ValueError("Соль не может быть пустой")
        self._salt = value
    
    @property
    def registration_date(self) -> datetime:
        """Геттер для даты регистрации."""
        return self._registration_date
    
    @registration_date.setter
    def registration_date(self, value: datetime) -> None:
        """Сеттер для даты регистрации."""
        if not isinstance(value, datetime):
            raise ValueError("Дата регистрации должна быть объектом datetime")
        self._registration_date = value
    
    def get_user_info(self) -> dict:
        """
        Возвращает информацию о пользователе (без пароля и соли).
        
        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat()
        }
    
    def change_password(self, new_password: str) -> None:
        """
        Изменяет пароль пользователя с хешированием.
        
        Args:
            new_password: Новый пароль
        """
        
        hashed = hashlib.sha256((new_password + self.salt).encode()).hexdigest()
        self.hashed_password = hashed
    
    def verify_password(self, password: str) -> bool:
        """
        Проверяет введённый пароль на совпадение.
        
        Args:
            password: Пароль для проверки
            
        Returns:
            True если пароль верный, иначе False
        """

        hashed_input = hashlib.sha256((password + self.salt).encode()).hexdigest()
        return hashed_input == self.hashed_password
    
    
class Wallet:
    """Класс кошелька пользователя для конкретной валюты."""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.
        
        Args:
            currency_code: Код валюты (например, "USD", "BTC")
            balance: Начальный баланс (по умолчанию 0.0)
        """
        self.currency_code = currency_code  
        self._balance = balance  
    
    @property
    def currency_code(self) -> str:
        """Геттер для кода валюты."""
        return self._currency_code
    
    @currency_code.setter
    def currency_code(self, value: str) -> None:
        """Сеттер для кода валюты."""
        if not value or not isinstance(value, str):
            raise ValueError("Код валюты не может быть пустым")
        if len(value.strip()) == 0:
            raise ValueError("Код валюты не может содержать только пробелы")
        self._currency_code = value.strip().upper()
    
    @property
    def balance(self) -> float:
        """Геттер для баланса."""
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        """Сеттер для баланса."""
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)
    
    def deposit(self, amount: float) -> None:
        """
        Пополнение баланса.
        
        Args:
            amount: Сумма для пополнения
            
        Raises:
            ValueError: Если сумма некорректна
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        
        self.balance += float(amount)
        print(f"Успешно пополнено {amount:.2f} {self.currency_code}")
    
    def withdraw(self, amount: float) -> bool:
        """
        Снятие средств с кошелька.
        
        Args:
            amount: Сумма для снятия
            
        Returns:
            True если снятие успешно, False если недостаточно средств
            
        Raises:
            ValueError: Если сумма некорректна
        """
        if not isinstance(amount, (int, float)):
            raise ValueError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        
        amount_float = float(amount)
        
        if amount_float > self.balance:
            print(f"Недостаточно средств. Баланс: {self.balance:.2f} {self.currency_code}")
            return False
        
        self.balance -= amount_float
        print(f"Успешно снято {amount_float:.2f} {self.currency_code}")
        return True
    
    def get_balance_info(self) -> str:
        """
        Возвращает информацию о текущем балансе.
        
        Returns:
            Строка с информацией о балансе
        """
        return f"Баланс {self.currency_code}: {self.balance:.2f}"

class Portfolio:
    """Класс портфеля для управления кошельками пользователя."""
    
    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Инициализация портфеля.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            wallets: Словарь кошельков (ключ - код валюты, значение - Wallet)
        """
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
    
    @property
    def user_id(self) -> int:
        """Геттер для ID пользователя."""
        return self._user_id
    
    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Геттер для словаря кошельков (возвращает копию)."""
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str) -> None:
        """
        Добавляет новый кошелёк в портфель.
        
        Args:
            currency_code: Код валюты
            
        Raises:
            ValueError: Если валюта уже существует в портфеле
        """
        if currency_code in self._wallets:
            raise ValueError(f"Валюта {currency_code} уже существует в портфеле")
        
        self._wallets[currency_code] = Wallet(currency_code=currency_code, balance=0.0)
    
    def get_total_value(self, base_currency: str = 'USD') -> float:
        """
        Возвращает общую стоимость всех валют в указанной базовой валюте.
        
        Args:
            base_currency: Код базовой валюты для конвертации
            
        Returns:
            Общая стоимость портфеля в базовой валюте
        """
        # Фиксированные курсы для упрощения
        exchange_rates = {
            'USD': {'USD': 1.0, 'EUR': 0.85, 'BTC': 0.000025, 'RUB': 0.011},
            'EUR': {'USD': 1.18, 'EUR': 1.0, 'BTC': 0.000029, 'RUB': 0.013},
            'BTC': {'USD': 40000.0, 'EUR': 34000.0, 'BTC': 1.0, 'RUB': 440000.0},
            'RUB': {'USD': 90.0, 'EUR': 77.0, 'BTC': 0.0000023, 'RUB': 1.0}
        }
        
        # Если базовая валюта не в курсах, используем USD как резерв
        if base_currency not in exchange_rates:
            base_currency = 'USD'
        
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code in exchange_rates:
                if base_currency in exchange_rates[currency_code]:
                    rate = exchange_rates[currency_code][base_currency]
                    total_value += wallet.balance * rate
                else:
                    usd_rate = exchange_rates[currency_code].get('USD', 1.0)
                    base_rate = exchange_rates['USD'].get(base_currency, 1.0)
                    total_value += wallet.balance * usd_rate * base_rate
            else:
                base_rate = exchange_rates['USD'].get(base_currency, 1.0)
                total_value += wallet.balance * base_rate
        
        return total_value
    
    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает объект Wallet по коду валюты.
        
        Args:
            currency_code: Код валюты
            
        Returns:
            Объект Wallet или None если кошелек не найден
        """
        return self._wallets.get(currency_code)