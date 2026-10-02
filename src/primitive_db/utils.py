import json
from pathlib import Path
from typing import Any

from src.primitive_db.constants import DATA_DIR


def get_table_path(table_name: str) -> Path:
    """Возвращает путь к JSON-файлу таблицы.

    Args:
        table_name: Имя таблицы.

    Returns:
        Путь к файлу таблицы в каталоге данных.
    """
    return DATA_DIR / f"{table_name}.json"


def load_json(filepath: str | Path, default: Any) -> Any:
    """Загружает JSON или возвращает значение для отсутствующего/повреждённого файла.

    Args:
        filepath: Путь к JSON-файлу.
        default: Значение для отсутствующего или повреждённого файла.

    Returns:
        Данные из файла или значение default.
    """
    try:
        with Path(filepath).open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(filepath: str | Path, data: Any) -> None:
    """Сохраняет данные в JSON-файл.

    Args:
        filepath: Путь к JSON-файлу.
        data: Данные для сохранения.
    """
    with Path(filepath).open("w", encoding="utf-8") as file:
        file.write(json.dumps(data))


def load_metadata(filepath: str) -> dict[str, Any]:
    """Загружает метаданные из JSON-файла.

    Args:
        filepath: Путь к JSON-файлу.

    Returns:
        Словарь с данными из файла.
    """
    return load_json(filepath, {})


def save_metadata(filepath: str, data: dict[str, Any]) -> None:
    """Сохраняет метаданные в JSON-файл.

    Args:
        filepath: Путь к JSON-файлу.
        data: Данные для сохранения.
    """
    save_json(filepath, data)


def load_table_data(table_name: str) -> list[dict[str, Any]]:
    """Загружает данные таблицы из JSON-файла.

    Args:
        table_name: Имя таблицы.

    Returns:
        Список записей таблицы.
    """
    return load_json(get_table_path(table_name), [])


def save_table_data(table_name: str, data: list[dict[str, Any]]) -> None:
    """Сохраняет данные таблицы в JSON-файл.

    Args:
        table_name: Имя таблицы.
        data: Данные для сохранения.
    """
    DATA_DIR.mkdir(exist_ok=True)
    save_json(get_table_path(table_name), data)


def delete_table_data(table_name: str) -> None:
    """Удаляет файл таблицы, если он существует.

    Args:
        table_name: Имя таблицы.
    """
    get_table_path(table_name).unlink(missing_ok=True)
