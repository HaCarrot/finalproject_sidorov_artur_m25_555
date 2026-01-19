import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from valutatrade_hub.core.usecases import (
    register_user,
    login_user,
    get_user_portfolio,
    buy_currency,
    sell_currency,
    get_exchange_rate
)


class CLIInterface:
    """Класс для обработки команд CLI."""
    
    def __init__(self):
        self.current_user: Optional[Dict[str, Any]] = None
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Создает парсер аргументов командной строки."""
        parser = argparse.ArgumentParser(
            description="ValutaTrade Hub - управление портфелем валют",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
        
        # Команда register
        register_parser = subparsers.add_parser("register", help="Регистрация нового пользователя")
        register_parser.add_argument("--username", type=str, required=True, help="Имя пользователя")
        register_parser.add_argument("--password", type=str, required=True, help="Пароль (минимум 4 символа)")
        
        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument("--username", type=str, required=True, help="Имя пользователя")
        login_parser.add_argument("--password", type=str, required=True, help="Пароль")
        
        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser("show-portfolio", help="Показать портфель пользователя")
        portfolio_parser.add_argument("--base", type=str, default="USD", help="Базовая валюта (по умолчанию: USD)")
        
        # Команда buy
        buy_parser = subparsers.add_parser("buy", help="Купить валюту")
        buy_parser.add_argument("--currency", type=str, required=True, help="Код покупаемой валюты (например, BTC)")
        buy_parser.add_argument("--amount", type=float, required=True, help="Количество покупаемой валюты")
        
        # Команда sell
        sell_parser = subparsers.add_parser("sell", help="Продать валюту")
        sell_parser.add_argument("--currency", type=str, required=True, help="Код продаваемой валюты")
        sell_parser.add_argument("--amount", type=float, required=True, help="Количество продаваемой валюты")
        
        # Команда get-rate
        rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
        rate_parser.add_argument("--from", type=str, required=True, dest="from_currency", help="Исходная валюта")
        rate_parser.add_argument("--to", type=str, required=True, dest="to_currency", help="Целевая валюта")
        
        return parser
    
    def _check_login(self) -> bool:
        """Проверяет, залогинен ли пользователь."""
        if not self.current_user:
            print("Сначала выполните login")
            return False
        return True
    
    def _validate_currency_code(self, code: str) -> bool:
        """Проверяет корректность кода валюты."""
        return bool(code and isinstance(code, str) and code.strip())
    
    def run(self) -> None:
        """Запускает обработку команд."""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            if args.command == "register":
                self.handle_register(args.username, args.password)
            elif args.command == "login":
                self.handle_login(args.username, args.password)
            elif args.command == "show-portfolio":
                self.handle_show_portfolio(args.base)
            elif args.command == "buy":
                self.handle_buy(args.currency, args.amount)
            elif args.command == "sell":
                self.handle_sell(args.currency, args.amount)
            elif args.command == "get-rate":
                self.handle_get_rate(args.from_currency, args.to_currency)
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)
    
    def handle_register(self, username: str, password: str) -> None:
        """Обрабатывает команду register."""
        try:
            user = register_user(username, password)
            print(f"Пользователь '{username}' зарегистрирован (id={user['user_id']}). Войдите: login --username {username} --password ****")
        except ValueError as e:
            print(f"{e}")
            sys.exit(1)
    
    def handle_login(self, username: str, password: str) -> None:
        """Обрабатывает команду login."""
        try:
            user = login_user(username, password)
            self.current_user = user
            print(f"Вы вошли как '{username}'")
        except ValueError as e:
            print(f"{e}")
            sys.exit(1)
    
    def handle_show_portfolio(self, base_currency: str) -> None:
        """Обрабатывает команду show-portfolio."""
        if not self._check_login():
            sys.exit(1)
        
        try:
            portfolio_info = get_user_portfolio(self.current_user["user_id"], base_currency)
            
            if not portfolio_info["wallets"]:
                print(f"Портфель пользователя '{self.current_user['username']}' пуст")
                return
            
            print(f"Портфель пользователя '{self.current_user['username']}' (база: {base_currency}):")
            
            total_value = 0.0
            for currency, info in portfolio_info["wallets"].items():
                if info["value_in_base"] is not None:
                    total_value += info["value_in_base"]
                    print(f"- {currency}: {info['balance']:.4f}  →  {info['value_in_base']:.2f} {base_currency}")
                else:
                    print(f"- {currency}: {info['balance']:.4f}  →  курс недоступен")
            
            print("-" * 40)
            print(f"ИТОГО: {total_value:,.2f} {base_currency}")
            
        except Exception as e:
            print(f"{e}")
            sys.exit(1)
    
    def handle_buy(self, currency: str, amount: float) -> None:
        """Обрабатывает команду buy."""
        if not self._check_login():
            sys.exit(1)
        
        if not self._validate_currency_code(currency):
            print("'currency' должен быть непустой строкой")
            sys.exit(1)
        
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            sys.exit(1)
        
        try:
            currency = currency.upper()
            result = buy_currency(self.current_user["user_id"], currency, amount)
            
            print(f"Покупка выполнена: {amount:.4f} {currency} по курсу {result['rate']:.2f} {result['base_currency']}/{currency}")
            print("Изменения в портфеле:")
            print(f"- {currency}: было {result['old_balance']:.4f} → стало {result['new_balance']:.4f}")
            if result['estimated_cost'] is not None:
                print(f"Оценочная стоимость покупки: {result['estimated_cost']:,.2f} {result['base_currency']}")
            
        except ValueError as e:
            print(f"Ошибка покупки: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Не удалось получить курс для {currency}→USD")
            sys.exit(1)
    
    def handle_sell(self, currency: str, amount: float) -> None:
        """Обрабатывает команду sell."""
        if not self._check_login():
            sys.exit(1)
        
        if not self._validate_currency_code(currency):
            print("'currency' должен быть непустой строкой")
            sys.exit(1)
        
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            sys.exit(1)
        
        try:
            currency = currency.upper()
            result = sell_currency(self.current_user["user_id"], currency, amount)
            
            print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {result['rate']:.2f} {result['base_currency']}/{currency}")
            print("Изменения в портфеле:")
            print(f"- {currency}: было {result['old_balance']:.4f} → стало {result['new_balance']:.4f}")
            if result['estimated_revenue'] is not None:
                print(f"Оценочная выручка: {result['estimated_revenue']:,.2f} {result['base_currency']}")
            
        except ValueError as e:
            error_msg = str(e)
            if "Недостаточно средств" in error_msg:
                print(error_msg)
            elif "У вас нет кошелька" in error_msg:
                print(f"{error_msg}. Добавьте валюту: она создаётся автоматически при первой покупке.")
            else:
                print(f"Ошибка продажи: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Не удалось получить курс для {currency}→USD")
            sys.exit(1)
    
    def handle_get_rate(self, from_currency: str, to_currency: str) -> None:
        """Обрабатывает команду get-rate."""
        if not self._validate_currency_code(from_currency) or not self._validate_currency_code(to_currency):
            print("Коды валют должны быть непустыми строками")
            sys.exit(1)
        
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            rate_info = get_exchange_rate(from_currency, to_currency)
            
            if rate_info["rate"] is None:
                print(f"Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже.")
                sys.exit(1)
            
            updated_at = datetime.fromisoformat(rate_info["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"Курс {from_currency}→{to_currency}: {rate_info['rate']:.8f} (обновлено: {updated_at})")
            
            if rate_info["rate"] != 0:
                reverse_rate = 1 / rate_info["rate"]
                print(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.8f}")
            
        except Exception as e:
            print(f"Ошибка получения курса: {e}")
            sys.exit(1)


def main():
    """Точка входа в CLI."""
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()