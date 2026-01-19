import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib
import secrets

from valutatrade_hub.core.models import User, Wallet, Portfolio


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


def _load_json(filepath: str, default: Any = None) -> Any:
    """Загружает данные из JSON файла."""
    if not os.path.exists(filepath):
        return default if default is not None else {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}


def _save_json(filepath: str, data: Any) -> None:
    """Сохраняет данные в JSON файл."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_salt() -> str:
    """Генерирует случайную соль."""
    return secrets.token_hex(8)


def _hash_password(password: str, salt: str) -> str:
    """Хеширует пароль с солью."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


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
        "registration_date": datetime.now().isoformat()
    }
    
    users.append(new_user)
    _save_json(USERS_FILE, users)
    
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    new_portfolio = {
        "user_id": user_id,
        "wallets": {}
    }
    portfolios.append(new_portfolio)
    _save_json(PORTFOLIOS_FILE, portfolios)
    
    return {
        "user_id": user_id,
        "username": username,
        "registration_date": new_user["registration_date"]
    }


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
        "registration_date": user_data["registration_date"]
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
        
        wallets_info[currency] = {
            "balance": balance,
            "value_in_base": value_in_base
        }
    
    return {
        "user_id": user_id,
        "base_currency": base_currency,
        "wallets": wallets_info
    }


def buy_currency(user_id: int, currency: str, amount: float) -> Dict[str, Any]:
    """Покупка валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    
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
    old_balance = wallets.get(currency, {}).get("balance", 0.0)
    new_balance = old_balance + amount
    
    wallets[currency] = {"balance": new_balance}
    portfolio_data["wallets"] = wallets
    portfolios[portfolio_idx] = portfolio_data
    _save_json(PORTFOLIOS_FILE, portfolios)
    
    rates_data = _load_json(RATES_FILE, {})
    base_currency = "USD"
    rate_key = f"{currency}_{base_currency}"
    rate = None
    estimated_cost = None
    
    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        rate = rates_data[rate_key]["rate"]
        estimated_cost = amount * rate
    
    return {
        "currency": currency,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "base_currency": base_currency,
        "rate": rate if rate is not None else 0.0,
        "estimated_cost": estimated_cost
    }


def sell_currency(user_id: int, currency: str, amount: float) -> Dict[str, Any]:
    """Продажа валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    
    portfolio_idx = -1
    portfolio_data = None
    for i, portfolio in enumerate(portfolios):
        if portfolio["user_id"] == user_id:
            portfolio_idx = i
            portfolio_data = portfolio
            break
    
    if portfolio_idx == -1:
        raise ValueError(f"У вас нет кошелька '{currency}'")
    
    wallets = portfolio_data.get("wallets", {})
    
    if currency not in wallets:
        raise ValueError(f"У вас нет кошелька '{currency}'")
    
    old_balance = wallets[currency].get("balance", 0.0)
    
    if amount > old_balance:
        raise ValueError(f"Недостаточно средств: доступно {old_balance:.4f} {currency}, требуется {amount:.4f}")
    
    new_balance = old_balance - amount
    
    if new_balance > 0:
        wallets[currency] = {"balance": new_balance}
    else:
        del wallets[currency]
    
    portfolio_data["wallets"] = wallets
    portfolios[portfolio_idx] = portfolio_data
    _save_json(PORTFOLIOS_FILE, portfolios)
    
    rates_data = _load_json(RATES_FILE, {})
    base_currency = "USD"
    rate_key = f"{currency}_{base_currency}"
    rate = None
    estimated_revenue = None
    
    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        rate = rates_data[rate_key]["rate"]
        estimated_revenue = amount * rate
    
    return {
        "currency": currency,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "base_currency": base_currency,
        "rate": rate if rate is not None else 0.0,
        "estimated_revenue": estimated_revenue
    }


def get_exchange_rate(from_currency: str, to_currency: str) -> Dict[str, Any]:
    """Получает курс обмена валют."""
    rates_data = _load_json(RATES_FILE, {})
    
    rate_key = f"{from_currency}_{to_currency}"
    
    if rate_key in rates_data:
        rate_info = rates_data[rate_key]
        updated_at = datetime.fromisoformat(rate_info["updated_at"])
        
        if datetime.now() - updated_at < timedelta(minutes=5):
            return {
                "from": from_currency,
                "to": to_currency,
                "rate": rate_info["rate"],
                "updated_at": rate_info["updated_at"],
                "source": "cache"
            }
    
    stub_rates = {
        "USD_EUR": {"rate": 0.85, "updated_at": datetime.now().isoformat()},
        "EUR_USD": {"rate": 1.18, "updated_at": datetime.now().isoformat()},
        "USD_BTC": {"rate": 0.000025, "updated_at": datetime.now().isoformat()},
        "BTC_USD": {"rate": 40000.0, "updated_at": datetime.now().isoformat()},
        "USD_RUB": {"rate": 90.0, "updated_at": datetime.now().isoformat()},
        "RUB_USD": {"rate": 0.011, "updated_at": datetime.now().isoformat()},
        "EUR_BTC": {"rate": 0.000029, "updated_at": datetime.now().isoformat()},
        "BTC_EUR": {"rate": 34000.0, "updated_at": datetime.now().isoformat()}
    }
    
    if rate_key in stub_rates:
        rate_info = stub_rates[rate_key]
        
        rates_data[rate_key] = rate_info
        rates_data["source"] = "ParserService"
        rates_data["last_refresh"] = datetime.now().isoformat()
        _save_json(RATES_FILE, rates_data)
        
        return {
            "from": from_currency,
            "to": to_currency,
            "rate": rate_info["rate"],
            "updated_at": rate_info["updated_at"],
            "source": "stub"
        }
    
    return {
        "from": from_currency,
        "to": to_currency,
        "rate": None,
        "updated_at": datetime.now().isoformat(),
        "source": None
    }