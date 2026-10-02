from pathlib import Path

# Имя файла для хранения метаданных БД.
METADATA_FILE = "db_meta.json"
# Путь к каталогу с данными таблиц.
DATA_DIR = Path("data")
# Название столбца с идентификатором записи.
ID_COLUMN = "ID"
# Соответствие имен типов типам Python.
TYPE_MAP = {"int": int, "str": str, "bool": bool}
# Множество поддерживаемых имен типов данных.
SUPPORTED_TYPES = set(TYPE_MAP)
# Допустимые символы в имени таблицы: латинские буквы, цифры и подчеркивание.
TABLE_NAME_PATTERN = r"[A-Za-z0-9_]+"
