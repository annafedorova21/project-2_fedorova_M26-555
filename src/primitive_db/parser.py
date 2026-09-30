import re
from typing import Any


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

    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
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


def parse_insert(command: str) -> dict[str, Any]:
    """Парсит insert-команду.

    Args:
        command: Insert-команда.

    Returns:
        Имя таблицы и значения новой записи.
    """
    try:
        prefix, raw_values = command.split(" values ", 1)
        _, _, table_name = prefix.split()
    except ValueError as error:
        raise ValueError(f"Некорректная insert-команда: {command}") from error

    raw_values = raw_values.strip()
    if not (raw_values.startswith("(") and raw_values.endswith(")")):
        raise ValueError(f"Некорректная insert-команда: {command}")

    return {
        "table_name": table_name,
        "values": [parse_value(value) for value in raw_values[1:-1].split(",")]
    }


def parse_select(command: str) -> dict[str, Any]:
    """Парсит select-команду.

    Args:
        command: Select-команда.

    Returns:
        Имя таблицы и условие отбора записей.
    """
    where_parts = command.split(" where ", 1)

    try:
        _, _, table_name = where_parts[0].split()
    except ValueError as error:
        raise ValueError(f"Некорректная select-команда: {command}") from error

    return {
        "table_name": table_name,
        "where_clause": (
            parse_clause(where_parts[1]) if len(where_parts) == 2 else None
        ),
    }


def parse_update(command: str) -> dict[str, Any]:
    """Парсит update-команду.

    Args:
        command: Update-команда.

    Returns:
        Имя таблицы, новые значения и условие отбора.
    """
    try:
        head, raw_where = command.split(" where ", 1)
        prefix, raw_set = head.split(" set ", 1)
        _, table_name = prefix.split()
    except ValueError as error:
        raise ValueError(f"Некорректная update-команда: {command}") from error

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
    try:
        prefix, raw_where = command.split(" where ", 1)
        _, _, table_name = prefix.split()
    except ValueError as error:
        raise ValueError(f"Некорректная delete-команда: {command}") from error

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
    try:
        _, table_name = command.split()
    except ValueError as error:
        raise ValueError(f"Некорректная info-команда: {command}") from error

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

    return parsers[action](command)
