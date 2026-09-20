# Contexto del proyecto md-to-logseq

**Fecha:** 2026-09-18

## Qué es

App Python/FastAPI con UI web para importar archivos `.md` directamente a Logseq usando su HTTP API local (puerto 12315).

## Estructura de archivos

```
C:\Users\Erick\md-to-logseq\
├── .env                    ← LOGSEQ_TOKEN y LOGSEQ_URL
├── CONTEXTO.md             ← este archivo
├── backend\
│   ├── main.py             ← FastAPI: GET /health, POST /import
│   ├── logseq_client.py    ← wrapper de la API de Logseq (timeout 60s)
│   ├── parser.py           ← Markdown → árbol de Block dataclasses
│   └── requirements.txt    ← fastapi, uvicorn, httpx, python-dotenv, python-multipart
└── frontend\
    └── index.html          ← UI drag & drop (vanilla JS, sirve desde FastAPI)
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
- `overwrite` (bool, default `false`) — sobreescribe la página si ya existe
- `filename_as_title` (bool, default `false`) — usa el nombre del archivo como título en vez del primer `# heading`

## Decisiones de diseño

- `appendBlockInPage` crea la página automáticamente si no existe → no se usa `createPage`.
- El parser extrae el título del primer `# heading`; si no hay heading usa el nombre del archivo.
- Jerarquía soportada: headings, párrafos, listas anidadas hasta 3 niveles, code fences, blockquotes.
- La UI se sirve desde el mismo FastAPI (no hay servidor separado para el frontend).

## Bugs resueltos

| Bug | Causa | Fix |
|---|---|---|
| `httpx.ReadTimeout` al importar | Timeout de 10s demasiado corto para Logseq | Timeout subido a 60s + `createPage` eliminado |

## Estado al 2026-09-18

- Dependencias instaladas (Python 3.11) ✅
- Servidor funcional en puerto 8000 ✅
- Logseq conectado y respondiendo ✅
- Importación end-to-end: **pendiente confirmar** después del fix de timeout
