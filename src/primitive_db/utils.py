import json
from pathlib import Path
from typing import Any

DATA_DIR = Path("data")


def load_metadata(filepath: str) -> dict[str, Any]:
    """Загружает метаданные из JSON-файла.

    Args:
        filepath: Путь к JSON-файлу.

    Returns:
        Словарь с данными из файла.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_metadata(filepath: str, data: dict[str, Any]) -> None:
    """Сохраняет метаданные в JSON-файл.

    Args:
        filepath: Путь к JSON-файлу.
        data: Данные для сохранения.
    """
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))


def load_table_data(table_name: str) -> list[dict[str, Any]]:
    """Загружает данные таблицы из JSON-файла.

    Args:
        table_name: Имя таблицы.

    Returns:
        Список записей таблицы.
    """
    try:
        filepath = DATA_DIR / f"{table_name}.json"
        with filepath.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_table_data(table_name: str, data: list[dict[str, Any]]) -> None:
    """Сохраняет данные таблицы в JSON-файл.

    Args:
        table_name: Имя таблицы.
        data: Данные для сохранения.
    """
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / f"{table_name}.json"
    with filepath.open("w", encoding="utf-8") as file:
        file.write(json.dumps(data))
