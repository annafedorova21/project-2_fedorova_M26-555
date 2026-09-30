from typing import Any

from src.primitive_db.utils import load_table_data

SUPPORTED_TYPES = {"int", "str", "bool"}


def table_exists(metadata: dict[str, Any], table_name: str) -> bool:
    """Проверяет существование таблицы.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя проверяемой таблицы

    Returns:
        Таблица существует или нет
    """
    if table_name in metadata:
        return True

    print(f'Ошибка: Таблица "{table_name}" не существует.')
    return False


def _matches(record: dict[str, Any], clause: dict[str, Any]) -> bool:
    """Проверяет, соответствует ли запись всем условиям фильтрации.

    Args:
        record: Проверяемая запись
        clause: Условия фильтрации

    Returns:
        Запись подходит под условие фильтрации.
    """
    return all(record.get(column) == value for column, value in clause.items())


def _is_valid_type(column: str, value: Any, expected_type: str) -> bool:
    """Проверяет тип переданного значения.

    Args:
        column: Имя столбца
        value: Проверяемое значение
        expected_type: Ожидаемый тип

    Returns:
        Значение является ожидаемым типом или нет
    """
    match expected_type:
        case "int":
            is_valid = type(value) is int
        case "str":
            is_valid = type(value) is str
        case "bool":
            is_valid = type(value) is bool
        case _:
            is_valid = False

    if not is_valid:
        print(
            f'Ошибка: Значение для столбца "{column}" должно иметь '
            f"тип {expected_type}."
        )
    return is_valid


def _is_supported_type(column_type: str) -> bool:
    """Проверяет, поддерживается ли тип столбца.

    Args:
        column_type: Тип столбца в строковом представлении

    Returns:
        Тип столбца поддерживается или нет
    """
    return column_type in SUPPORTED_TYPES


def insert(
    metadata: dict[str, Any],
    table_name: str,
    values: list[Any],
) -> list[dict[str, Any]]:
    """Добавляет запись в таблицу.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        values: Значения новой записи

    Returns:
        Список записей таблицы с добавленной записью
    """
    if not table_exists(metadata, table_name):
        return []

    table_data = load_table_data(table_name)
    schema = metadata[table_name]
    user_columns = [column for column in schema if column != "ID"]

    if len(values) != len(user_columns):
        print(
            "Ошибка: Количество значений не соответствует количеству "
            "столбцов таблицы."
        )
        return table_data

    for column, value in zip(user_columns, values):
        expected_type = schema[column]
        if not _is_valid_type(column, value, expected_type):
            return table_data

    new_id = max(
        (record.get("ID", 0) for record in table_data),
        default=0,
    ) + 1
    record = {"ID": new_id}
    record.update(dict(zip(user_columns, values)))
    return [*table_data, record]


def select(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Возвращает записи, подходящие под условие запроса.

    Args:
        table_data: Записи таблицы
        where_clause: Условия фильтрации записей

    Returns:
        Записи, соответствующие условиям фильтрации
    """
    if where_clause is None:
        return table_data
    return [record for record in table_data if _matches(record, where_clause)]


def update(
    table_data: list[dict[str, Any]],
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> list[dict[str, Any]]:
    """Обновляет поля записей, подходящих под условие фильтрации.

    Args:
        table_data: Записи таблицы
        set_clause: Новые значения полей
        where_clause: Условия фильтрации записей

    Returns:
        Список всех записей таблицы после обновления.
    """
    return [
        {**record, **set_clause} if _matches(record, where_clause) else record
        for record in table_data
    ]


def delete(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any],
) -> list[dict[str, Any]]:
    """Удаляет записи, подходящие под условие.

    Args:
        table_data: Записи таблицы
        where_clause: Условия отбора удаляемых записей

    Returns:
        Список оставшихся записей таблицы.
    """
    return [
        record
        for record in table_data
        if not _matches(record, where_clause)
    ]


def create_table(
    metadata: dict[str, Any], table_name: str, columns: list[str]
) -> dict[str, Any]:
    """Создает таблицу.

    Args:
        metadata: Текущие метаданные БД
        table_name: Имя создаваемой таблицы
        columns: Список столбцов

    Returns:
        Обновленный словарь метаданных БД
    """
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed_columns = {"ID": "int"}
    for column in columns:
        try:
            column_name, column_type = column.split(":", maxsplit=1)
        except (AttributeError, ValueError):
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        if not _is_supported_type(column_type):
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        parsed_columns[column_name] = column_type

    metadata[table_name] = parsed_columns
    columns_description = ", ".join(
        f"{column_name}:{column_type}"
        for column_name, column_type in parsed_columns.items()
    )
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{columns_description}"
    )

    return metadata


def list_tables(metadata: dict[str, Any]) -> None:
    """Выводит список созданных таблиц.

    Args:
        metadata: Метаданные базы данных
    """
    for table_name in metadata:
        print(f"- {table_name}")


def drop_table(metadata: dict[str, Any], table_name: str) -> dict[str, Any]:
    """Удаляет таблицу из метаданных.

    Args:
        metadata: Текущие метаданные базы данных
        table_name: Имя удаляемой таблицы

    Returns:
        Обновленный словарь метаданных.
    """
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata
