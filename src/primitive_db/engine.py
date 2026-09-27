import shlex

from src.primitive_db.core import create_table, drop_table, list_tables
from src.primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    """Выводит справку по доступным командам."""
    print("***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


def run() -> None:
    """Запускает основной цикл программы."""
    print_help()

    while True:
        metadata = load_metadata(METADATA_FILE)
        user_input = input("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            print("Введите команду.")
            continue

        command, *command_args = args

        match command:
            case "exit":
                break
            case "help":
                print_help()
            case "list_tables":
                list_tables(metadata)
            case "create_table":
                if len(command_args) < 2:
                    invalid_value = " ".join(command_args)
                    print(
                        f"Некорректное значение: {invalid_value}. Попробуйте снова."
                    )
                    continue

                table_name, *columns = command_args
                updated_metadata = create_table(metadata, table_name, columns)
                save_metadata(METADATA_FILE, updated_metadata)
            case "drop_table":
                if len(command_args) != 1:
                    invalid_value = " ".join(command_args)
                    print(
                        f"Некорректное значение: {invalid_value}. Попробуйте снова."
                    )
                    continue

                updated_metadata = drop_table(metadata, command_args[0])
                save_metadata(METADATA_FILE, updated_metadata)
            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
