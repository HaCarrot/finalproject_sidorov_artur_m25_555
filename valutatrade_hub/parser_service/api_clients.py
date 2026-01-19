import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов."""
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы валют от API.
        
        Returns:
            Словарь с курсами в формате {"FROM_TO": rate}
            
        Raises:
            ApiRequestError: При ошибке API
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API."""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def fetch_rates(self) -> Dict[str, float]:
        """Получает курсы криптовалют от CoinGecko."""
        try:
            # Формируем параметры запроса
            ids = ",".join(
                self.config.CRYPTO_ID_MAP.get(currency, currency.lower())
                for currency in self.config.CRYPTO_CURRENCIES
            )
            
            params = {
                "ids": ids,
                "vs_currencies": self.config.BASE_CURRENCY.lower()
            }
            
            # Отправляем запрос
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Проверяем статус
            if response.status_code != 200:
                raise ApiRequestError(
                    f"CoinGecko API error: {response.status_code} - {response.text}"
                )
            
            # Парсим ответ
            data = response.json()
            rates = {}
            
            for currency in self.config.CRYPTO_CURRENCIES:
                coin_id = self.config.CRYPTO_ID_MAP.get(currency, currency.lower())
                if coin_id in data:
                    rate = data[coin_id].get(self.config.BASE_CURRENCY.lower())
                    if rate is not None:
                        pair_key = f"{currency}_{self.config.BASE_CURRENCY}"
                        rates[pair_key] = float(rate)
            
            return rates
            
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko network error: {str(e)}")
        except (ValueError, KeyError) as e:
            raise ApiRequestError(f"CoinGecko parsing error: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API."""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def fetch_rates(self) -> Dict[str, float]:
        """Получает курсы фиатных валют от ExchangeRate-API."""
        try:
            # Формируем URL
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
            
            # Отправляем запрос
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Проверяем статус
            if response.status_code != 200:
                data = response.json()
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(
                    f"ExchangeRate-API error: {response.status_code} - {error_type}"
                )
            
            # Парсим ответ
            data = response.json()
            rates = {}
            
            if "conversion_rates" in data:
                for currency in self.config.FIAT_CURRENCIES:
                    if currency in data["conversion_rates"]:
                        rate = data["conversion_rates"][currency]
                        pair_key = f"{currency}_{self.config.BASE_CURRENCY}"
                        rates[pair_key] = float(rate)
            
            return rates
            
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API network error: {str(e)}")
        except (ValueError, KeyError) as e:
            raise ApiRequestError(f"ExchangeRate-API parsing error: {str(e)}")