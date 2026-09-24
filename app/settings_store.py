import json
import logging
import os
from threading import Lock

from app import config

logger = logging.getLogger("expmon.settings")

_DEFAULTS = {
    "data_path": config.DATA_PATH_DEFAULT,
    "refresh_ms": config.REFRESH_MS_DEFAULT,
    "auto_refresh": "0",
}

_CACHE: dict[str, str] = dict(_DEFAULTS)
_LOCK = Lock()
_LOADED = False


def _load():
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        if os.path.exists(config.SETTINGS_FILE):
            with open(config.SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in _CACHE:
                    _CACHE[k] = v
    except Exception:
        logger.debug("No se pudieron leer los settings; usando defaults.", exc_info=True)


def get(key: str, default=None):
    _load()
    return _CACHE.get(key, default)


def data_path() -> str:
    return get("data_path", config.DATA_PATH_DEFAULT) or ""


def refresh_ms() -> int:
    try:
        return int(get("refresh_ms", config.REFRESH_MS_DEFAULT) or config.REFRESH_MS_DEFAULT)
    except (TypeError, ValueError):
        return config.REFRESH_MS_DEFAULT


def auto_refresh() -> bool:
    return str(get("auto_refresh", "0")) in ("1", "true", "True")


def settings() -> dict:
    _load()
    return {
        "data_path": data_path(),
        "refresh_ms": refresh_ms(),
        "auto_refresh": auto_refresh(),
    }


def set(**values) -> None:
    _load()
    changed = False
    for k, v in values.items():
        if k in _CACHE and str(v) != str(_CACHE[k]):
            _CACHE[k] = str(v)
            changed = True
    if not changed:
        return
    with _LOCK:
        try:
            parent = os.path.dirname(config.SETTINGS_FILE) or "."
            os.makedirs(parent, exist_ok=True)
            with open(config.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(_CACHE, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.warning("No se pudo guardar los settings: %s", exc)