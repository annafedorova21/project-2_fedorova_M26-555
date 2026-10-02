import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import prompt

FuncParams = ParamSpec("FuncParams")
FuncReturn = TypeVar("FuncReturn")

def handle_db_errors(
    func: Callable[FuncParams, FuncReturn],
) -> Callable[FuncParams, FuncReturn | None]:
    """Перехватывает ошибки при работе с БД."""

    @wraps(func)
    def wrapper(*args: FuncParams.args, **kwargs: FuncParams.kwargs) -> FuncReturn | None:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. Возможно, база данных "
                "не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except SyntaxError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return

    return wrapper


def confirm_action(
    action_name: str,
) -> Callable[
    [Callable[FuncParams, FuncReturn]],
    Callable[FuncParams, FuncReturn | None],
]:
    """Запрашивает подтверждение перед выполнением опасной операции."""

    def decorator(
        call: Callable[FuncParams, FuncReturn],
    ) -> Callable[FuncParams, FuncReturn | None]:
        @wraps(call)
        def wrapper(
            *args: FuncParams.args,
            **kwargs: FuncParams.kwargs,
        ) -> FuncReturn | None:
            confirmation_prompt = (
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )
            answer = prompt.string(prompt=confirmation_prompt)
            if answer != "y":
                print("Операция отменена.")
                return

            return call(*args, **kwargs)

        return wrapper

    return decorator


def log_time(
    call: Callable[FuncParams, FuncReturn],
) -> Callable[FuncParams, FuncReturn]:
    """Выводит время выполнения функции."""

    @wraps(call)
    def wrapper(
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> FuncReturn:
        start = time.monotonic()
        try:
            return call(*args, **kwargs)
        finally:
            end = time.monotonic() - start
            print(
                f"Функция {call.__name__} выполнилась за "
                f"{end:.3f} секунд."
            )

    return wrapper


def create_cacher():
    """Возвращает функции кэширования и очистки общего кэша в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Кеширует результат."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    def clear():
        """Очищает кеш."""
        cache.clear()

    return cache_result, clear
