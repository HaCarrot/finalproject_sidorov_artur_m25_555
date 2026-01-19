class InsufficientFundsError(Exception):
    """Исключение для недостатка средств."""

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = f"Недостаточно средств: доступно {available:.4f} {code}, требуется {required:.4f} {code}" #noqa: E501
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Исключение для неизвестной валюты."""

    def __init__(self, code: str):
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Исключение для ошибок внешнего API."""

    def __init__(self, reason: str = ""):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)
