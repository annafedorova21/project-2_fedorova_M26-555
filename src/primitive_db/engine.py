import shlex
from typing import Any

from prettytable import PrettyTable

from src.primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    table_exists,
    update,
)
from src.primitive_db.parser import parse_crud_command
from src.primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    """Выводит справку по доступным командам."""
    print("***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = "
        "<значение> - прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = "
        "<новое_значение1> where <столбец_условия> = "
        "<значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = "
        "<значение> - удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


def handle_insert(
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
    new_data = insert(metadata, table_name, values)

    save_table_data(table_name, new_data)
    print(
        f"Запись с ID={new_data[-1]['ID']} успешно добавлена "
        f'в таблицу "{table_name}".'
    )


def handle_select(
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
    rows = select(load_table_data(table_name), where_clause)
    columns = list(metadata[table_name])

    result_table = PrettyTable(columns)
    result_table.add_rows(
        [
            row.get(column) for column in columns
        ]
            for row in rows
    )
    print(result_table)


def handle_update(
    table_name: str,
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> None:
    """Обновляет записи таблицы и сохраняет данные.

    Args:
        table_name: Имя таблицы
        set_clause: Новые значения полей
        where_clause: Условие отбора записей
    """
    table_data = load_table_data(table_name)
    selected_records = select(table_data, where_clause)

    if not selected_records:
        print("Записи, соответствующие условию, не найдены.")
        return

    new_data = update(table_data, set_clause, where_clause)
    save_table_data(table_name, new_data)

    for record in selected_records:
        print(
            f'Запись с ID={record["ID"]} в таблице "{table_name}" '
            "успешно обновлена."
        )


def handle_delete(
    table_name: str,
    where_clause: dict[str, Any],
) -> None:
    """Удаляет записи из таблицы и сохраняет данные.

    Args:
        table_name: Имя таблицы
        where_clause: Условие отбора записей
    """
    table_data = load_table_data(table_name)
    selected_records = select(table_data, where_clause)

    if not selected_records:
        print("Записи, соответствующие условию, не найдены.")
        return

    updated_data = delete(table_data, where_clause)
    save_table_data(table_name, updated_data)

    for record in selected_records:
        print(
            f"Запись с ID={record['ID']} успешно удалена "
            f'из таблицы "{table_name}".'
        )


def handle_info(
    metadata: dict[str, Any],
    table_name: str,
) -> None:
    """Выводит информацию о таблице.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
    """
    schema = metadata[table_name]
    columns = ", ".join(
        f"{column}:{column_type}"
        for column, column_type in schema.items()
    )

    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns}")
    print(
        f"Количество записей: "
        f"{len(load_table_data(table_name))}"
    )


def crud_operation(
    metadata: dict[str, Any],
    user_input: str,
    action: str,
) -> None:
    """Выполняет CRUD-команду.

    Args:
        metadata: Метаданные базы данных
        user_input: Введенная пользователем команда
        action: Тип CRUD-операции
    """
    try:
        parsed_command = parse_crud_command(user_input, action)
        table_name = parsed_command["table_name"]

        if not table_exists(metadata, table_name):
            print(f"Таблицы {table_name} не существует. Попробуйте снова.")
            return

        match action:
            case "insert":
                handle_insert(metadata, table_name, parsed_command["values"])
            case "select":
                handle_select(metadata, table_name, parsed_command["where_clause"])
            case "update":
                handle_update(
                    table_name,
                    parsed_command["set_clause"],
                    parsed_command["where_clause"],
                )
            case "delete":
                handle_delete(table_name, parsed_command["where_clause"])
            case "info":
                handle_info(metadata, table_name)

    except (KeyError, IndexError, ValueError) as error:
        print(f"Ошибка: {error}")


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


def handle_create_table(
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
    updated_metadata = create_table(metadata, table_name, columns)
    save_metadata(METADATA_FILE, updated_metadata)


def handle_drop_table(
    metadata: dict[str, Any],
    command_args: list[str],
) -> None:
    """Удаляет таблицу по аргументам команды.

    Args:
        metadata: Метаданные базы данных
        command_args: Аргументы команды
    """
    if not check_args("drop_table", command_args):
        return
    if not table_exists(metadata, command_args[0]):
        return

    updated_metadata = drop_table(metadata, command_args[0])
    save_metadata(METADATA_FILE, updated_metadata)


def run() -> None:
    print_help()

    while True:
        metadata = load_metadata(METADATA_FILE)
        user_input = input(">>> Введите команду: ")

        if not user_input.strip():
            print("Введите команду.")
            continue

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        command, *command_args = args

        match command:
            case "insert" | "select" | "update" | "delete" | "info":
                crud_operation(metadata, user_input, command)
            case "exit":
                break
            case "help":
                print_help()
            case "list_tables":
                list_tables(metadata)
            case "create_table":
                handle_create_table(metadata, command_args)
            case "drop_table":
                handle_drop_table(metadata, command_args)
            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
