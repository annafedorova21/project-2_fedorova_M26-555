import json


def load_metadata(filepath: str) -> dict:
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


def save_metadata(filepath: str, data: dict) -> None:
    """Сохраняет метаданные в JSON-файл.

    Args:
        filepath: Путь к JSON-файлу.
        data: Данные для сохранения.
    """
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))
