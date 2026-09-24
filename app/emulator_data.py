import json
import os

MAX_POINTS = 3000
MAX_SEARCH_DEPTH = 8

EMULATOR_FILES = ("db_emulator.json", "EMULATOR_state.json", "EMULATOR_config.json")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".idea", ".vscode", "venv", ".venv"}

SPECIES_LABELS = {
    "Xv": "Xv",
    "Glucose": "Glucosa",
    "Ethanol": "Etanol",
    "V": "Volumen",
    "e": "e",
    "Si": "Si",
}

# Especies que se plotean (como en Plot_emulator_state.py)
PLOT_SPECIES = ("Xv", "Glucose")

PALETTE = (
    "#0ea5e9", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
)


def _has_file(directory: str, filename: str) -> bool:
    return os.path.isfile(os.path.join(directory, filename))


def _find_dir_with_files(path: str) -> str:
    if all(_has_file(path, f) for f in EMULATOR_FILES):
        return path
    base_depth = path.rstrip(os.sep).count(os.sep)
    best = None
    best_depth = None
    for root, dirs, files in os.walk(path):
        depth = root.rstrip(os.sep).count(os.sep) - base_depth
        if depth >= MAX_SEARCH_DEPTH:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if best is not None and depth >= best_depth:
            dirs[:] = []
            continue
        if all(f in files for f in EMULATOR_FILES):
            best = root
            best_depth = depth
    if best is None:
        names = ", ".join(EMULATOR_FILES)
        raise FileNotFoundError(
            f"No se encontraron los archivos del emulador ({names}) en '{path}' "
            f"ni en sus subdirectorios (hasta {MAX_SEARCH_DEPTH} niveles)."
        )
    return best


def _read(path: str, filename: str):
    full = os.path.join(path, filename)
    if not os.path.isfile(full):
        raise FileNotFoundError(f"No se encontró el archivo '{filename}' en '{path}'.")
    with open(full, encoding="utf-8") as f:
        return json.load(f)


def _downsample(points, max_points=MAX_POINTS):
    points = sorted(points, key=lambda p: p[0])
    if len(points) <= max_points:
        return points
    step = len(points) / max_points
    return [points[int(i * step)] for i in range(max_points)]


def _series(series_id, label, unit, points, style="line", color=None):
    return {
        "series_id": series_id,
        "label": label,
        "unit": unit,
        "type": "float",
        "style": style,
        "dashed": style == "dashed",
        "color": color,
        "points": points,
    }


def load_emulator(path: str) -> dict:
    emulator_dir = _find_dir_with_files(path)
    db = _read(emulator_dir, "db_emulator.json")
    state = _read(emulator_dir, "EMULATOR_state.json")
    config = _read(emulator_dir, "EMULATOR_config.json")

    reactors = [r for r in db.keys() if r in state]
    if not reactors:
        raise ValueError("No hay biorreactores comunes entre db_emulator.json y EMULATOR_state.json.")

    species_list = [sp for sp in PLOT_SPECIES if sp in (config.get("Species_list") or [])]
    od_factor = config.get("OD_factor") or {}

    charts = []
    for reactor in reactors:
        color_idx = 0

        def next_color():
            nonlocal color_idx
            color = PALETTE[color_idx % len(PALETTE)]
            color_idx += 1
            return color

        agg = db[reactor].get("measurements_aggregated", {})
        reactor_state = state.get(reactor, {})
        all_state = reactor_state.get("All", {})

        series = []
        for sp in species_list:
            name = SPECIES_LABELS.get(sp, sp)
            if sp in all_state:
                tw = zip(all_state[sp].get("time", []), all_state[sp].get("Value", []))
                model = [[t, v] for t, v in tw if v is not None]
                series.append(_series(
                    f"{reactor}/{sp}/modelo",
                    f"{name} (modelo)",
                    "g/l",
                    _downsample(model),
                    color=next_color(),
                ))
            real = None
            if sp == "Xv" and "OD" in agg and od_factor.get(reactor):
                tw = zip(agg["OD"].get("measurement_time", []), agg["OD"].get("OD", []))
                real = [[t, v / od_factor[reactor]] for t, v in tw if v is not None]
            elif sp in agg:
                tw = zip(agg[sp].get("measurement_time", []), agg[sp].get(sp, []))
                real = [[t, v] for t, v in tw if v is not None]
            if real:
                series.append(_series(
                    f"{reactor}/{sp}/real",
                    f"{name} (medición)",
                    "g/l",
                    _downsample(real),
                    style="dots",
                    color=next_color(),
                ))

        if "Feed_meas" in agg:
            tw = zip(agg["Feed_meas"].get("measurement_time", []), agg["Feed_meas"].get("Feed_meas", []))
            feed = [[t, v] for t, v in tw if v is not None]
            series.append(_series(
                f"{reactor}/Feed/real",
                "Feed (medición)",
                "g/l",
                feed,
                style="stars",
                color=next_color(),
            ))

        charts.append({
            "id": reactor,
            "label": reactor,
            "current": reactor_state.get("Current", {}),
            "series": [s for s in series if s["points"]],
        })

    return {
        "source": "emulador",
        "exp_name": config.get("exp_name", ""),
        "time": state.get("time"),
        "iter": state.get("iter"),
        "experiment_duration": config.get("experiment_duration"),
        "charts": [c for c in charts if c["series"]],
    }