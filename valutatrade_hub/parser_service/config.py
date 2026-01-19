import os
from dataclasses import dataclass


@dataclass
class ParserConfig:
    """Конфигурация для Parser Service."""
    
    # API ключи (загружаются из переменных окружения)
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "5304e79baeaf0f789351bde7")
    
    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB", "JPY", "CNY")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL", "LTC", "XRP")
    
    # Сопоставление кодов криптовалют с ID для CoinGecko
    CRYPTO_ID_MAP: dict = {
        "BTC": "bitcoin",
        "ETH": "ethereum", 
        "SOL": "solana",
        "LTC": "litecoin",
        "XRP": "ripple"
    }
    
    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    
    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 1