import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config, emulator_data, settings_store
from app.templating import now_utc, templates

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=config.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {
        "request": request,
        "app_name": config.APP_NAME,
        "now": now_utc(),
        "tz_name": config.TIMEZONE,
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


class PlotRequest(BaseModel):
    path: str
    emulador: bool = True


@app.post("/api/plot")
def api_plot(req: PlotRequest):
    path = req.path.strip()
    if not path:
        return {"error": "Indicá el nombre de la ejecución (ej. Pio_emu)."}
    if not req.emulador:
        return {"error": "El caso sin emulador aún no está implementado."}
    resolved = config.resolve_data_path(path)
    try:
        data = emulator_data.load_emulator(resolved)
        data["path"] = config.display_data_path(resolved)
        return data
    except FileNotFoundError as e:
        return {"error": str(e).replace(resolved, path)}
    except Exception as e:
        return {"error": f"Error al procesar la ejecución '{path}': {e}"}


@app.get("/api/runs")
def api_runs():
    base = config.DATA_PATH_DEFAULT
    if not base or not os.path.isdir(base):
        return {"runs": []}
    try:
        runs = sorted(
            d for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d)) and not d.startswith(".")
        )
    except OSError:
        runs = []
    return {"runs": runs}


def _settings_public() -> dict:
    s = settings_store.settings()
    s["data_path"] = config.display_data_path(s.get("data_path") or "")
    return s


@app.get("/api/settings")
def api_settings():
    return _settings_public()


@app.post("/api/settings")
async def api_settings_save(request: Request):
    body = await request.json()
    raw = str(body.get("data_path", "")).strip()
    if raw:
        settings_store.set(data_path=config.display_data_path(raw))
    if "auto_refresh" in body:
        settings_store.set(auto_refresh="1" if bool(body.get("auto_refresh")) else "0")
    if "refresh_secs" in body:
        try:
            secs = max(1, int(body.get("refresh_secs")))
        except (TypeError, ValueError):
            secs = max(1, config.REFRESH_MS_DEFAULT // 1000)
        settings_store.set(refresh_ms=secs * 1000)
    return _settings_public()


@app.get("/")
def index(request: Request):
    return render(
        request,
        "monitor.html",
        {
            "data_path": config.display_data_path(settings_store.data_path()),
            "base_dir": config.DATA_PATH_DEFAULT,
            "auto_refresh": settings_store.auto_refresh(),
            "refresh_secs": max(1, settings_store.refresh_ms() // 1000),
        },
    )