import re
from typing import Any

from prettytable import PrettyTable

from src.primitive_db.constants import (
    ID_COLUMN,
    METADATA_FILE,
    TABLE_NAME_PATTERN,
    TYPE_MAP,
)
from src.primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from src.primitive_db.utils import (
    delete_table_data,
    load_table_data,
    save_metadata,
    save_table_data,
)

cache, clear_cache = create_cacher()


def _matches(record: dict[str, Any], clause: dict[str, Any]) -> bool:
    """Проверяет, соответствует ли запись всем условиям фильтрации.

    Args:
        record: Проверяемая запись
        clause: Условия фильтрации

    Returns:
        Запись подходит под условие фильтрации.
    """
    return all(record.get(column) == value for column, value in clause.items())


def validate_values(schema: dict[str, str], values: dict[str, Any]) -> None:
    """Проверяет соответствие столбцов и типов значений схеме таблицы.

    Args:
        schema: Имена и типы столбцов таблицы.
        values: Проверяемые значения по именам столбцов.
    """

    for column, value in values.items():
        expected_type = schema[column]
        if type(value) is not TYPE_MAP[expected_type]:
            raise ValueError(
                f'Значение для столбца "{column}" должно иметь тип {expected_type}.'
            )


def handle_insert(
    metadata: dict[str, Any],
    table_name: str,
    values: list[Any],
) -> list[dict[str, Any]]:
    """Добавляет запись, сохраняет таблицу и сбрасывает кэш.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        values: Значения новой записи

    Returns:
        Список записей таблицы с добавленной записью
    """
    schema = metadata[table_name]
    table_data = load_table_data(table_name)
    user_columns = [column for column in schema if column != ID_COLUMN]

    if len(values) != len(user_columns):
        raise ValueError(
            "Количество значений не соответствует количеству столбцов таблицы."
        )

    validate_values(schema, dict(zip(user_columns, values)))

    new_id = (
        max(
            (record.get(ID_COLUMN, 0) for record in table_data),
            default=0,
        )
        + 1
    )
    record = {ID_COLUMN: new_id}
    record.update(dict(zip(user_columns, values)))
    data = [*table_data, record]
    save_table_data(table_name, data)
    clear_cache()
    return data


def handle_select(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any] | None = None,
    *,
    schema: dict[str, str],
    table_name: str,
) -> list[dict[str, Any]]:
    """Возвращает записи по условию запроса с кэшированием результата.

    Args:
        table_data: Записи таблицы
        table_name: Имя таблицы
        where_clause: Условия фильтрации записей
        schema: Имена и типы столбцов таблицы

    Returns:
        Записи, соответствующие условиям фильтрации
    """
    validate_values(schema, where_clause or {})
    key = f"{table_name}:{where_clause}"
    return cache(
        key,
        lambda: (
            table_data
            if where_clause is None
            else [record for record in table_data if _matches(record, where_clause)]
        ),
    )


def handle_update(
    table_data: list[dict[str, Any]],
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
    *,
    schema: dict[str, str],
) -> list[dict[str, Any]]:
    """Обновляет поля записей, подходящих под условие фильтрации.

    Args:
        table_data: Записи таблицы
        set_clause: Новые значения полей
        where_clause: Условия фильтрации записей
        schema: Имена и типы столбцов таблицы

    Returns:
        Список всех записей таблицы после обновления.
    """
    if ID_COLUMN in set_clause:
        raise ValueError(f'Изменение столбца "{ID_COLUMN}" запрещено.')

    validate_values(schema, set_clause)
    validate_values(schema, where_clause)

    return [
        {**record, **set_clause} if _matches(record, where_clause) else record
        for record in table_data
    ]


def handle_delete(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any],
    *,
    schema: dict[str, str],
) -> list[dict[str, Any]]:
    """Удаляет записи, подходящие под условие.

    Args:
        table_data: Записи таблицы
        where_clause: Условия отбора удаляемых записей
        schema: Имена и типы столбцов таблицы

    Returns:
        Список оставшихся записей таблицы.
    """
    validate_values(schema, where_clause)

    return [record for record in table_data if not _matches(record, where_clause)]


def handle_create_table(
    metadata: dict[str, Any], table_name: str, columns: list[str]
) -> dict[str, Any] | None:
    """Создает таблицу.

    Args:
        metadata: Текущие метаданные БД
        table_name: Имя создаваемой таблицы
        columns: Список столбцов

    Returns:
        Обновленный словарь метаданных БД
    """
    if re.fullmatch(TABLE_NAME_PATTERN, table_name) is None:
        print(f"Некорректное значение: {table_name}. Попробуйте снова.")
        return None

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed_columns = {ID_COLUMN: "int"}
    for column in columns:
        column_name, column_type = column.split(":", maxsplit=1)
        parsed_columns[column_name] = column_type

    metadata[table_name] = parsed_columns

    save_metadata(METADATA_FILE, metadata)

    columns_description = ", ".join(
        f"{column_name}:{column_type}"
        for column_name, column_type in parsed_columns.items()
    )
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_description}')

    return metadata


def list_tables(metadata: dict[str, Any]) -> None:
    """Выводит имена созданных таблиц."""
    if not metadata:
        print("Таблиц в базе данных нет.")
    for table_name in metadata:
        print(f"- {table_name}")


def handle_drop_table(
    metadata: dict[str, Any], table_name: str
) -> dict[str, Any] | None:
    """Удаляет таблицу из метаданных.

    Args:
        metadata: Текущие метаданные базы данных
        table_name: Имя удаляемой таблицы

    Returns:
        Обновленный словарь метаданных.
    """
    del metadata[table_name]

    save_metadata(METADATA_FILE, metadata)
    delete_table_data(table_name)

    clear_cache()

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


@log_time
@handle_db_errors
def insert(
    metadata: dict[str, Any],
    table_name: str,
    values: list[Any],
) -> None:
    """Добавляет запись в таблицу и сохраняет данные.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        values: Значения новой записи
    """
    new_data = handle_insert(metadata, table_name, values)
    if new_data is None:
        return

    print(
        f"Запись с ID={new_data[-1][ID_COLUMN]} успешно добавлена "
        f'в таблицу "{table_name}".'
    )


@log_time
@handle_db_errors
def select(
    metadata: dict[str, Any],
    table_name: str,
    where_clause: dict[str, Any] | None,
) -> None:
    """Выводит записи таблицы, подходящие под условие.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        where_clause: Условие отбора записей
    """
    schema = metadata[table_name]
    table_data = load_table_data(table_name)
    columns = list(schema)

    result_table = PrettyTable(columns)
    result_table.add_rows(
        [row.get(column) for column in columns]
        for row in handle_select(
            table_data, where_clause, schema=schema, table_name=table_name
        )
    )
    print(result_table)


@handle_db_errors
def update(
    metadata: dict[str, Any],
    table_name: str,
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> None:
    """Обновляет записи таблицы и сохраняет данные.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        set_clause: Новые значения полей
        where_clause: Условие отбора записей
    """
    schema = metadata[table_name]
    table_data = load_table_data(table_name)
    updated = handle_update(table_data, set_clause, where_clause, schema=schema)
    if updated is None:
        return
    updated_records = handle_select(
        table_data, where_clause, schema=schema, table_name=table_name
    )
    if not updated_records:
        print("Записи, соответствующие условию, не найдены.")
        return
    save_table_data(table_name, updated)
    clear_cache()

    for record in updated_records:
        print(
            f'Запись с ID={record[ID_COLUMN]} в таблице "{table_name}" '
            "успешно обновлена."
        )


@handle_db_errors
@confirm_action("удаление записи")
def delete(
    metadata: dict[str, Any],
    table_name: str,
    where_clause: dict[str, Any],
) -> None:
    """Удаляет записи из таблицы и сохраняет данные.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        where_clause: Условие отбора записей
    """
    schema = metadata[table_name]
    table_data = load_table_data(table_name)
    deleted_records = handle_select(
        table_data, where_clause, schema=schema, table_name=table_name
    )
    if not deleted_records:
        print("Записи, соответствующие условию, не найдены.")
        return
    updated = handle_delete(table_data, where_clause, schema=schema)
    if updated is None:
        return
    save_table_data(table_name, updated)
    clear_cache()

    for record in deleted_records:
        print(
            f"Запись с ID={record[ID_COLUMN]} успешно удалена "
            f'из таблицы "{table_name}".'
        )


@handle_db_errors
def info(
    metadata: dict[str, Any],
    table_name: str,
) -> None:
    """Выводит информацию о таблице.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
    """
    schema = metadata[table_name]
    record_count = len(load_table_data(table_name))
    columns = ", ".join(
        f"{column}:{column_type}" for column, column_type in schema.items()
    )

    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns}")
    print(f"Количество записей: {record_count}")


def check_args(command: str, command_args: list[str]) -> bool:
    """Проверяет аргументы команды управления таблицей.

    Args:
        command: Имя команды
        command_args: Аргументы команды

    Returns:
        Аргументы команды указаны корректно или нет
    """
    match command:
        case "create_table":
            is_valid = len(command_args) >= 2
        case "drop_table":
            is_valid = len(command_args) == 1
        case _:
            is_valid = False

    if not is_valid:
        invalid_value = " ".join(command_args)
        print(f"Некорректное значение: {invalid_value}. Попробуйте снова.")

    return is_valid


@handle_db_errors
def create_table(
    metadata: dict[str, Any],
    command_args: list[str],
) -> None:
    """Создает таблицу по аргументам команды.

    Args:
        metadata: Метаданные базы данных
        command_args: Аргументы команды
    """
    if not check_args("create_table", command_args):
        return

    table_name, *columns = command_args
    handle_create_table(metadata, table_name, columns)


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(
    metadata: dict[str, Any],
    command_args: list[str],
) -> None:
    """Удаляет таблицу по аргументам команды.

    Args:
        metadata: Метаданные базы данных
        command_args: Аргументы команды

    Returns:
        None.
    """
    if not check_args("drop_table", command_args):
        return

    table_name = command_args[0]
    handle_drop_table(metadata, table_name)
