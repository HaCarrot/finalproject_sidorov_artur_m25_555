import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger("domain.actions")


def log_action(
    action: str, verbose: bool = False, log_exceptions: bool = True
) -> Callable:
    """
    Декоратор для логирования доменных операций.

    Args:
        action: Название действия (BUY/SELL/REGISTER/LOGIN и т.д.)
        verbose: Добавлять подробный контекст в логи
        log_exceptions: Логировать исключения
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_context: Dict[str, Any] = {
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "result": "OK",
            }

            try:
                result = func(*args, **kwargs)

                if isinstance(result, dict):
                    for field in [
                        "user_id",
                        "username",
                        "currency",
                        "amount",
                        "rate",
                        "base_currency",
                    ]:
                        if field in result:
                            log_context[field] = result[field]

                    if verbose:
                        for field in [
                            "old_balance",
                            "new_balance",
                            "estimated_cost",
                            "estimated_revenue",
                        ]:
                            if field in result:
                                log_context[field] = result[field]

                logger.info(_format_log_message(log_context))

                return result

            except Exception as e:
                if log_exceptions:
                    log_context["result"] = "ERROR"
                    log_context["error_type"] = type(e).__name__
                    log_context["error_message"] = str(e)

                    _extract_args_to_context(args, kwargs, log_context)

                    logger.error(_format_log_message(log_context))
                    logger.debug(f"Traceback for {action}: {traceback.format_exc()}")

                raise

        return wrapper

    return decorator


def _format_log_message(context: Dict[str, Any]) -> str:
    """
    Форматирует сообщение лога в строку.

    Args:
        context: Контекст для логирования

    Returns:
        Отформатированная строка лога
    """
    parts = [f"action={context.get('action', 'UNKNOWN')}"]

    for field in ["user_id", "username", "currency", "amount", "rate", "base_currency"]:
        if field in context:
            parts.append(f"{field}={context[field]}")

    parts.append(f"result={context.get('result', 'UNKNOWN')}")

    if context.get("result") == "ERROR":
        error_info = []
        if "error_type" in context:
            error_info.append(context["error_type"])
        if "error_message" in context:
            error_info.append(context["error_message"])
        if error_info:
            parts.append(f"error={' '.join(error_info)}")

    return " ".join(parts)


def _extract_args_to_context(
    args: tuple, kwargs: dict, context: Dict[str, Any]
) -> None:
    """
    Извлекает информацию из аргументов функции в контекст лога.

    Args:
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        context: Контекст для обновления
    """
    for arg in args:
        if isinstance(arg, int) and "user_id" not in context:
            context["user_id"] = arg
            break

    for arg in args:
        if (
            isinstance(arg, str)
            and arg.isupper()
            and len(arg) <= 5
            and "currency" not in context
        ):
            context["currency"] = arg
            break

    for arg in args:
        if isinstance(arg, (int, float)) and "amount" not in context:
            context["amount"] = arg
            break

    for key in ["user_id", "username", "currency", "amount", "rate", "base_currency"]:
        if key in kwargs and key not in context:
            context[key] = kwargs[key]
