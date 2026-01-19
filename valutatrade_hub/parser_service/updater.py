import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.api_clients import BaseApiClient


logger = logging.getLogger("parser.updater")


class RatesUpdater:
    """Класс для обновления курсов валют."""
    
    def __init__(
        self,
        config: ParserConfig,
        clients: Dict[str, BaseApiClient],
        storage: Any
    ):
        self.config = config
        self.clients = clients
        self.storage = storage
        self.all_rates = {}
    
    def run_update(self, source: str = None) -> Dict[str, Any]:
        """
        Запускает обновление курсов.
        
        Args:
            source: Источник для обновления (coingecko, exchangerate, или None для всех)
            
        Returns:
            Словарь с результатами обновления
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        logger.info(f"Starting rates update at {timestamp}")
        
        results = {
            "success": {},
            "errors": {},
            "total_rates": 0
        }
        
        # Определяем какие источники обновлять
        sources_to_update = []
        if source:
            if source.lower() == "coingecko" and "coingecko" in self.clients:
                sources_to_update = ["coingecko"]
            elif source.lower() == "exchangerate" and "exchangerate" in self.clients:
                sources_to_update = ["exchangerate"]
            else:
                raise ValueError(f"Unknown source: {source}")
        else:
            sources_to_update = list(self.clients.keys())
        
        # Обновляем каждый источник
        for source_name in sources_to_update:
            client = self.clients[source_name]
            
            try:
                logger.info(f"Fetching rates from {source_name}...")
                rates = client.fetch_rates()
                
                # Добавляем метаданные
                for pair_key, rate in rates.items():
                    rate_entry = {
                        "rate": rate,
                        "updated_at": timestamp,
                        "source": source_name.title()
                    }
                    self.all_rates[pair_key] = rate_entry
                
                results["success"][source_name] = len(rates)
                results["total_rates"] += len(rates)
                logger.info(f"Successfully fetched {len(rates)} rates from {source_name}")
                
            except ApiRequestError as e:
                error_msg = str(e)
                results["errors"][source_name] = error_msg
                logger.error(f"Failed to fetch from {source_name}: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                results["errors"][source_name] = error_msg
                logger.error(f"Unexpected error from {source_name}: {error_msg}")
        
        # Сохраняем данные
        if self.all_rates:
            try:
                final_data = {
                    "pairs": self.all_rates,
                    "last_refresh": timestamp,
                    "source": "ParserService"
                }
                
                self.storage.save_current_rates(final_data)
                self.storage.save_to_history(self.all_rates, timestamp)
                
                logger.info(f"Successfully saved {len(self.all_rates)} rates")
                
            except Exception as e:
                error_msg = f"Failed to save rates: {str(e)}"
                results["errors"]["storage"] = error_msg
                logger.error(error_msg)
        
        return results