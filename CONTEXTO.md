# Contexto del proyecto md-to-logseq

**Fecha:** 2026-09-20

## Qué es

App Python/FastAPI con UI web para importar archivos `.md` directamente a Logseq usando su HTTP API local (puerto 12315).

## Estructura de archivos

```
C:\Users\Erick\md-to-logseq\
├── .env                    ← LOGSEQ_TOKEN y LOGSEQ_URL
├── .gitignore              ← excluye .env, logs, archivos temporales
├── CONTEXTO.md             ← este archivo
├── backend\
│   ├── main.py             ← FastAPI: GET /health, POST /import
│   ├── logseq_client.py    ← wrapper async de la API de Logseq
│   ├── parser.py           ← Markdown → árbol de Block dataclasses
│   └── requirements.txt    ← fastapi, uvicorn, httpx, python-dotenv, python-multipart
└── frontend\
    └── index.html          ← UI drag & drop con grupos y tags (vanilla JS)
```

## Cómo iniciar

```powershell
cd C:\Users\Erick\md-to-logseq\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Abrir en el navegador: http://127.0.0.1:8000

> Requisito: Logseq debe estar abierto con la HTTP API activa.
> `Settings → Features → HTTP APIs server`

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Verifica conexión con Logseq |
| POST | `/import` | Recibe `.md`, parsea e inserta bloques en Logseq |

Parámetros de `/import`:
- `overwrite` (bool, default `false`) — elimina la página existente y la recrea
- `filename_as_title` (bool, default `false`) — usa el nombre del archivo como título
- `tags` (string, default `""`) — agrega `tags:: <valor>` como primer bloque

## Decisiones de diseño

- `appendBlockInPage` crea la página automáticamente si no existe → no se usa `createPage`.
- El parser extrae el título del primer `# heading`; si no hay heading usa el nombre del archivo.
- Jerarquía soportada: headings, párrafos, listas con anidamiento arbitrario, code fences, blockquotes.
- La UI se sirve desde el mismo FastAPI (no hay servidor separado para el frontend).
- El API de Logseq es single-threaded: `_api_sem = asyncio.Semaphore(1)` en `logseq_client.py` serializa todas las llamadas para evitar saturar su cola interna.
- La UI soporta múltiples grupos, cada uno con su propio tag y lista de archivos.

## Bugs resueltos

| Bug | Causa | Fix |
|---|---|---|
| `httpx.ReadTimeout` al importar | `httpx.post` síncrono bloqueaba el event loop de FastAPI | Migrado a `httpx.AsyncClient` con `await` |
| `overwrite=True` duplicaba bloques | No se eliminaba la página antes de reimportar | Agrega llamada a `delete_page()` cuando `overwrite=True` |
| Anidamiento > 3 niveles se perdía | Loops hardcodeados de 3 niveles en `main.py` | Inserción de hijos recursiva con `_insert_children()` |
| Imports paralelos saturaban Logseq | Múltiples requests concurrentes llenaban la cola del API | Semáforo global `asyncio.Semaphore(1)` en `logseq_client._call` |

## Estado al 2026-09-20

- Dependencias instaladas (Python 3.11) ✅
- Servidor funcional en puerto 8000 ✅
- Logseq conectado y respondiendo ✅
- Importación end-to-end confirmada ✅
- Importación paralela (5 archivos, 3 concurrentes): 54s, 0 errores ✅
- Repositorio: https://github.com/elperegrino/md-to-logseq ✅
