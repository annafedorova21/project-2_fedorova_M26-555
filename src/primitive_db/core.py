from typing import Any

SUPPORTED_TYPES = {"int", "str", "bool"}


def create_table(
    metadata: dict[str, Any], table_name: str, columns: list[str]
) -> dict[str, Any]:
    """Создает таблицу и добавляет ее описание в метаданные.

    Args:
        metadata: Текущие метаданные базы данных
        table_name: Имя создаваемой таблицы
        columns: Список столбцов в формате имя:тип
    Returns:
        Обновленный словарь метаданных.
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

        if not column_name or column_type not in SUPPORTED_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        if column_name in parsed_columns:
            print(f"Некорректное значение: {column_name}. Попробуйте снова.")
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
    """Выводит список созданных таблиц."""
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
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata
