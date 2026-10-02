import shlex
from typing import Any

import prompt

from src.primitive_db.constants import METADATA_FILE
from src.primitive_db.core import (
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    select,
    update,
)
from src.primitive_db.decorators import handle_db_errors
from src.primitive_db.parser import parse_crud_command
from src.primitive_db.utils import load_metadata


def print_help() -> None:
    """Выводит справку по доступным командам.

    Returns:
        None.
    """
    print("***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец:тип> ... - создать таблицу.")
    print("<command> list_tables - показать список всех таблиц.")
    print("<command> drop_table <имя_таблицы> - удалить таблицу.")
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


@handle_db_errors
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
    parsed_command = parse_crud_command(user_input, action)
    table_name = parsed_command["table_name"]

    match action:
        case "insert":
            insert(metadata, table_name, parsed_command["values"])
        case "select":
            select(metadata, table_name, parsed_command["where_clause"])
        case "update":
            update(
                metadata,
                table_name,
                parsed_command["set_clause"],
                parsed_command["where_clause"],
            )
        case "delete":
            delete(metadata, table_name, parsed_command["where_clause"])
        case "info":
            info(metadata, table_name)


def run() -> None:
    """Запускает цикл обработки команд."""
    print_help()

    while True:
        metadata = load_metadata(METADATA_FILE)
        user_input = prompt.string(prompt=">>> Введите команду: ", empty=False)

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
                create_table(metadata, command_args)
            case "drop_table":
                drop_table(metadata, command_args)
            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
