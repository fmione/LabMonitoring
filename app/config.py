import os

APP_NAME = os.environ.get("EXPMON_APP_NAME", "ExpMonitor")
HOST = os.environ.get("EXPMON_HOST", "0.0.0.0")
PORT = int(os.environ.get("EXPMON_PORT", "8000"))

DATA_PATH_DEFAULT = os.environ.get("EXPMON_DATA_DIR", "")
REFRESH_MS_DEFAULT = int(os.environ.get("EXPMON_REFRESH_MS", "5000"))
TIMEZONE = os.environ.get("EXPMON_TZ", "Etc/GMT+3")

SETTINGS_FILE = os.environ.get(
    "EXPMON_SETTINGS_FILE",
    os.path.join(os.path.dirname(__file__), "settings.json"),
)


def resolve_data_path(user_input: str) -> str:
    """Resuelve la ruta ingresada: absoluta se usa tal cual; relativa se
    resuelve contra el directorio base (EXPMON_DATA_DIR)."""
    p = (user_input or "").strip()
    if not p or os.path.isabs(p):
        return p
    if DATA_PATH_DEFAULT:
        return os.path.join(DATA_PATH_DEFAULT, p)
    return p


def display_data_path(full: str) -> str:
    """Devuelve la ruta como la ve el usuario: relativa si está dentro del
    directorio base, absoluta si no."""
    if not full or not DATA_PATH_DEFAULT:
        return full or ""
    try:
        rel = os.path.relpath(full, DATA_PATH_DEFAULT)
    except ValueError:
        return full
    if rel == ".":
        return ""
    if rel == ".." or rel.startswith(".." + os.sep):
        return full
    return rel