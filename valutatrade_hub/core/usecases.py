import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

from valutatrade_hub.core.currencies import CurrencyNotFoundError, get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    InsufficientFundsError,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import settings

USERS_FILE = settings.get_users_file()
PORTFOLIOS_FILE = settings.get_portfolios_file()
RATES_FILE = settings.get_rates_file()


def _load_json(filepath: str, default: Any = None) -> Any:
    """Загружает данные из JSON файла."""
    if not os.path.exists(filepath):
        return default if default is not None else {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}


def _save_json(filepath: str, data: Any) -> None:
    """Сохраняет данные в JSON файл."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_salt() -> str:
    """Генерирует случайную соль."""
    return secrets.token_hex(8)


def _hash_password(password: str, salt: str) -> str:
    """Хеширует пароль с солью."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


@log_action(action="REGISTER", verbose=True, log_exceptions=True)
def register_user(username: str, password: str) -> Dict[str, Any]:
    """Регистрирует нового пользователя."""
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = _load_json(USERS_FILE, [])

    for user in users:
        if user["username"] == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    if users:
        user_id = max(u["user_id"] for u in users) + 1
    else:
        user_id = 1

    salt = _generate_salt()
    hashed_password = _hash_password(password, salt)

    new_user = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat(),
    }

    users.append(new_user)
    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    new_portfolio = {"user_id": user_id, "wallets": {}}
    portfolios.append(new_portfolio)
    _save_json(PORTFOLIOS_FILE, portfolios)

    return {
        "user_id": user_id,
        "username": username,
        "registration_date": new_user["registration_date"],
    }


@log_action(action="LOGIN", verbose=False, log_exceptions=True)
def login_user(username: str, password: str) -> Dict[str, Any]:
    """Вход пользователя в систему."""
    users = _load_json(USERS_FILE, [])

    user_data = None
    for user in users:
        if user["username"] == username:
            user_data = user
            break

    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    salt = user_data["salt"]
    hashed_input = _hash_password(password, salt)

    if hashed_input != user_data["hashed_password"]:
        raise ValueError("Неверный пароль")

    return {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "registration_date": user_data["registration_date"],
    }


def get_user_portfolio(user_id: int, base_currency: str = "USD") -> Dict[str, Any]:
    """Получает портфель пользователя."""
    portfolios = _load_json(PORTFOLIOS_FILE, [])

    portfolio_data = None
    for portfolio in portfolios:
        if portfolio["user_id"] == user_id:
            portfolio_data = portfolio
            break

    if not portfolio_data:
        portfolio_data = {"user_id": user_id, "wallets": {}}

    rates_data = _load_json(RATES_FILE, {})

    wallets_info = {}
    for currency, wallet_data in portfolio_data.get("wallets", {}).items():
        balance = wallet_data.get("balance", 0.0)

        value_in_base = None
        if currency != base_currency:
            rate_key = f"{currency}_{base_currency}"
            if rate_key in rates_data and "rate" in rates_data[rate_key]:
                value_in_base = balance * rates_data[rate_key]["rate"]
            elif currency == "USD" and base_currency != "USD":
                usd_key = f"{currency}_USD"
                if usd_key in rates_data and "rate" in rates_data[usd_key]:
                    usd_value = balance * rates_data[usd_key]["rate"]
                    base_key = f"USD_{base_currency}"
                    if base_key in rates_data and "rate" in rates_data[base_key]:
                        value_in_base = usd_value * rates_data[base_key]["rate"]
        elif currency == base_currency:
            value_in_base = balance

        wallets_info[currency] = {"balance": balance, "value_in_base": value_in_base}

    return {"user_id": user_id, "base_currency": base_currency, "wallets": wallets_info}


@log_action(action="BUY", verbose=True, log_exceptions=True)
def buy_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Покупка валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(currency_code)

    portfolios = _load_json(PORTFOLIOS_FILE, [])

    portfolio_idx = -1
    portfolio_data = None
    for i, portfolio in enumerate(portfolios):
        if portfolio["user_id"] == user_id:
            portfolio_idx = i
            portfolio_data = portfolio
            break

    if portfolio_idx == -1:
        portfolio_data = {"user_id": user_id, "wallets": {}}
        portfolios.append(portfolio_data)
        portfolio_idx = len(portfolios) - 1

    wallets = portfolio_data.get("wallets", {})
    old_balance = wallets.get(currency_code, {}).get("balance", 0.0)
    new_balance = old_balance + amount

    wallets[currency_code] = {"balance": new_balance}
    portfolio_data["wallets"] = wallets
    portfolios[portfolio_idx] = portfolio_data
    _save_json(PORTFOLIOS_FILE, portfolios)

    rates_data = _load_json(RATES_FILE, {})
    base_currency = "USD"
    rate_key = f"{currency_code}_{base_currency}"
    rate = None
    estimated_cost = None

    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        rate = rates_data[rate_key]["rate"]
        estimated_cost = amount * rate

    return {
        "user_id": user_id,
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "base_currency": base_currency,
        "rate": rate if rate is not None else 0.0,
        "estimated_cost": estimated_cost,
    }


@log_action(action="SELL", verbose=True, log_exceptions=True)
def sell_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Продажа валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(currency_code)

    portfolios = _load_json(PORTFOLIOS_FILE, [])

    portfolio_idx = -1
    portfolio_data = None
    for i, portfolio in enumerate(portfolios):
        if portfolio["user_id"] == user_id:
            portfolio_idx = i
            portfolio_data = portfolio
            break

    if portfolio_idx == -1:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    wallets = portfolio_data.get("wallets", {})

    if currency_code not in wallets:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    old_balance = wallets[currency_code].get("balance", 0.0)

    if amount > old_balance:
        raise InsufficientFundsError(
            available=old_balance, required=amount, code=currency_code
        )

    new_balance = old_balance - amount

    if new_balance > 0:
        wallets[currency_code] = {"balance": new_balance}
    else:
        del wallets[currency_code]

    portfolio_data["wallets"] = wallets
    portfolios[portfolio_idx] = portfolio_data
    _save_json(PORTFOLIOS_FILE, portfolios)

    rates_data = _load_json(RATES_FILE, {})
    base_currency = "USD"
    rate_key = f"{currency_code}_{base_currency}"
    rate = None
    estimated_revenue = None

    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        rate = rates_data[rate_key]["rate"]
        estimated_revenue = amount * rate

    return {
        "user_id": user_id,
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "base_currency": base_currency,
        "rate": rate if rate is not None else 0.0,
        "estimated_revenue": estimated_revenue,
    }


def get_exchange_rate(from_code: str, to_code: str) -> Dict[str, Any]:
    """Получает курс обмена валют."""
    try:
        get_currency(from_code)
        get_currency(to_code)
    except CurrencyNotFoundError as e:
        raise CurrencyNotFoundError(
            str(e).replace("Валюта с кодом", "Неизвестная валюта")
        )

    rates_data = _load_json(RATES_FILE, {})

    rate_key = f"{from_code}_{to_code}"

    if rate_key in rates_data:
        rate_info = rates_data[rate_key]
        updated_at = datetime.fromisoformat(rate_info["updated_at"])

        ttl_seconds = settings.get_rates_ttl()
        if datetime.now() - updated_at < timedelta(seconds=ttl_seconds):
            return {
                "from": from_code,
                "to": to_code,
                "rate": rate_info["rate"],
                "updated_at": rate_info["updated_at"],
                "source": "cache",
            }

    stub_rates = {
        "USD_EUR": {"rate": 0.85, "updated_at": datetime.now().isoformat()},
        "EUR_USD": {"rate": 1.18, "updated_at": datetime.now().isoformat()},
        "USD_BTC": {"rate": 0.000025, "updated_at": datetime.now().isoformat()},
        "BTC_USD": {"rate": 40000.0, "updated_at": datetime.now().isoformat()},
        "USD_RUB": {"rate": 90.0, "updated_at": datetime.now().isoformat()},
        "RUB_USD": {"rate": 0.011, "updated_at": datetime.now().isoformat()},
        "EUR_BTC": {"rate": 0.000029, "updated_at": datetime.now().isoformat()},
        "BTC_EUR": {"rate": 34000.0, "updated_at": datetime.now().isoformat()},
    }

    if rate_key in stub_rates:
        rate_info = stub_rates[rate_key]

        rates_data[rate_key] = rate_info
        rates_data["source"] = "ParserService"
        rates_data["last_refresh"] = datetime.now().isoformat()
        _save_json(RATES_FILE, rates_data)

        return {
            "from": from_code,
            "to": to_code,
            "rate": rate_info["rate"],
            "updated_at": rate_info["updated_at"],
            "source": "stub",
        }

    raise ApiRequestError(f"Курс {from_code}→{to_code} недоступен")
