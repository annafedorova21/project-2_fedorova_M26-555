import re
from typing import Any

from src.primitive_db.constants import TABLE_NAME_PATTERN


def parse_value(value: str) -> Any:
    """Преобразует строковое значение в поддерживаемый тип.

    Args:
        value: Значение для приведения к типу

    Returns:
        Значение необходимого типа (int, str, bool).
    """
    value = value.strip()
    normalized_value = value.lower()

    if normalized_value in {"true", "false"}:
        return normalized_value == "true"

    if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
        return value[1:-1]

    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Некорректное значение: {value}. "
            "Строковые значения должны быть в кавычках."
        )


def parse_clause(clause: str) -> dict[str, Any]:
    """Разбирает условие вида column = value.

    Args:
        clause: Условие

    Returns:
        Словарь с именем столбца и значением.
    """
    match = re.fullmatch(r"\s*([A-Za-zА-Яа-я_]\w*)\s*=\s*(.+?)\s*", clause)
    if match is None:
        raise ValueError(f"Некорректное условие: {clause}")

    column, raw_value = match.groups()

    return {column: parse_value(raw_value)}


def parse_values(raw_values: str) -> list[Any]:
    """Разбирает значения, разделённые запятыми.

    Args:
        raw_values: Строка значений, разделённых запятыми.

    Returns:
        Список значений, преобразованных в поддерживаемые типы.
    """
    return [parse_value(value) for value in raw_values.split(",")]


def _match_command(command: str, pattern: str) -> re.Match[str]:
    """Проверяет полную структуру команды и извлекает её аргументы.

    Args:
        command: Проверяемая команда.
        pattern: Регулярное выражение для проверки структуры команды.

    Returns:
        Объект совпадения с аргументами команды в группах.
    """
    match = re.fullmatch(pattern, command.strip())
    if match is None:
        raise ValueError(f"Некорректная команда: {command}")
    return match


def parse_insert(command: str) -> dict[str, Any]:
    """Парсит insert-команду.

    Args:
        command: Insert-команда.

    Returns:
        Имя таблицы и значения новой записи.
    """
    table_name, raw_values = _match_command(
        command, rf"insert\s+into\s+({TABLE_NAME_PATTERN})\s+values\s*\((.*)\)"
    ).groups()

    return {
        "table_name": table_name,
        "values": parse_values(raw_values),
    }


def parse_select(command: str) -> dict[str, Any]:
    """Парсит select-команду.

    Args:
        command: Select-команда.

    Returns:
        Имя таблицы и условие отбора записей.
    """
    table_name, raw_where = _match_command(
        command, rf"select\s+from\s+({TABLE_NAME_PATTERN})(?:\s+where\s+(.+))?"
    ).groups()

    return {
        "table_name": table_name,
        "where_clause": parse_clause(raw_where) if raw_where is not None else None,
    }


def parse_update(command: str) -> dict[str, Any]:
    """Парсит update-команду.

    Args:
        command: Update-команда.

    Returns:
        Имя таблицы, новые значения и условие отбора.
    """
    table_name, raw_set, raw_where = _match_command(
        command,
        rf"update\s+({TABLE_NAME_PATTERN})\s+set\s+(.+?)\s+where\s+(.+)",
    ).groups()

    return {
        "table_name": table_name,
        "set_clause": parse_clause(raw_set),
        "where_clause": parse_clause(raw_where),
    }


def parse_delete(command: str) -> dict[str, Any]:
    """Парсит delete-команду.

    Args:
        command: Delete-команда.

    Returns:
        Имя таблицы и условие отбора записей.
    """
    table_name, raw_where = _match_command(
        command, rf"delete\s+from\s+({TABLE_NAME_PATTERN})\s+where\s+(.+)"
    ).groups()

    return {
        "table_name": table_name,
        "where_clause": parse_clause(raw_where),
    }


def parse_info(command: str) -> dict[str, Any]:
    """Парсит info-команду.

    Args:
        command: Info-команда.

    Returns:
        Имя таблицы.
    """
    table_name = _match_command(command, rf"info\s+({TABLE_NAME_PATTERN})").group(1)

    return {"table_name": table_name}


def parse_crud_command(command: str, action: str) -> dict[str, Any]:
    """Передает CRUD-команду соответствующему парсеру.

    Args:
        command: CRUD-команда.
        action: Тип CRUD-операции.

    Returns:
        Разобранные параметры команды.
    """
    parsers = {
        "insert": parse_insert,
        "select": parse_select,
        "update": parse_update,
        "delete": parse_delete,
        "info": parse_info,
    }

    try:
        return parsers[action](command)
    except ValueError as error:
        raise SyntaxError(command) from error
