# ExpMonitor

Aplicación web de monitoreo de experimentos en tiempo real. Muestra los datos
reales de una ejecución local y plotea las predicciones del modelo frente a los
datos reales. Sin autenticación.

Apariencia visual basada en el proyecto LabManager (FastAPI + Jinja2 +
Bootstrap 5 + Chart.js, todo offline, sin CDN ni paso de build).

## Pantalla única: Monitoreo

Un solo input con el **nombre de la ejecución**, un switch para **incluir el
emulador** y un botón **Plotear**. También hay un switch de **Auto-refresh**
con un campo de segundos (por defecto `EXPMON_REFRESH_MS`): al activarlo la app
re-plotea periódicamente sin intervención. El directorio base (montado desde
`EXPMON_DATA_DIR_HOST`) es un detalle interno: escribís solo el nombre (ej.
`Pio_emu`) y la app lo resuelve contra esa base. Al plotear con el emulador
activado, la app busca en la ejecución los archivos:

- `db_emulator.json` — mediciones reales agregadas por biorreactor
- `EMULATOR_state.json` — estado de la simulación del emulador
- `EMULATOR_config.json` — configuración (especies, factor OD, etc.)

y grafica por biorreactor las variables del modelo **Xv** y **Glucose** (línea
sólida) contra las mediciones reales (puntos), incluyendo la conversión
`OD → Xv` con el `OD_factor` de la config y los eventos de `Feed_meas` como
marcadores (`*`). El caso **sin emulador** se implementará más adelante.

Ejemplo: con `EXPMON_DATA_DIR_HOST=/home/fede/Documentos/Airflow`, al escribir
`Pio_emu` la app resuelve a
`/home/fede/Documentos/Airflow/Pio_emu/dags/scripts/emulator_dag`
(busca los 3 archivos recursivamente) y grafica los biorreactores.

## Puesta en marcha (Docker Compose)

```bash
cp .env.example .env    # o editar el .env existente
docker compose up --build
```

La web queda en <http://localhost:8100>.

`EXPMON_DATA_DIR_HOST` define el directorio **base** del host donde viven las
ejecuciones (vive fuera de este proyecto). Se monta en `/data` dentro del
contenedor; la app guarda el último nombre usado en
`/data/.expmon-settings.json` (sobrevive a rebuilds y queda junto a los datos).

En Docker no escribís `/data` en la web: ingresás el nombre de la ejecución
(relativo a la base), como `Pio_emu`.

### Desarrollo local (sin Docker)

```bash
source .venv/bin/activate
EXPMON_DATA_DIR=/home/fede/Documentos/Airflow uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acá `EXPMON_DATA_DIR` cumple el rol de directorio base con el mismo comportamiento
(escribís `Pio_emu` en la web). Si preferís rutas absolutas, escribilas tal cual.

### Desarrollo con Docker (hot reload, sin rebuild)

El `docker-compose.override.yml` (se aplica automáticamente) monta `./app` en el
contenedor y ejecuta uvicorn con `--reload`: al modificar código la app se
recarga sola, no hace falta rebuild. Si cambiás `requirements.txt`, ahí sí
corré `docker compose up --build`.

```bash
docker compose up
```

## API

- `POST /api/plot` — body `{path, emulador}`. `path` es el nombre de la
  ejecución (relativo) o una ruta absoluta; la app lo resuelve contra el
  directorio base. Lee los archivos del emulador y devuelve
  `{source, exp_name, time, iter, charts: [...]}` con una lista de series
  `{label, unit, type, dashed, points: [[t, v], ...]}` por biorreactor.
- `GET/POST /api/settings` — lectura/escritura del último nombre usado.

## Configuración

Variables de entorno (opcionales, definidas en `.env`):

- `EXPMON_DATA_DIR_HOST` — ruta **absoluta** del directorio BASE de ejecuciones en el host (fuera del proyecto; se monta en `/data`).
- `EXPMON_PORT` — puerto web en el host (por defecto `8100`).
- `EXPMON_DATA_DIR` — directorio base dentro del contenedor (por defecto `/data`); contra él se resuelven los nombres de ejecución. En local sin Docker apuntalo al mismo directorio base del host.
- `EXPMON_REFRESH_MS` — intervalo de refresco por defecto (ms).
- `EXPMON_TZ` — zona horaria (por defecto `Etc/GMT+3`).
- `EXPMON_SETTINGS_FILE` — dónde guardar la configuración persistida.