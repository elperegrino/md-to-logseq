import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from logseq_client import LogseqClient
from parser import parse_markdown

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

LOGSEQ_TOKEN = os.getenv("LOGSEQ_TOKEN", "")
LOGSEQ_URL = os.getenv("LOGSEQ_URL", "http://127.0.0.1:12315")

app = FastAPI(title="md-to-logseq")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def get_client() -> LogseqClient:
    if not LOGSEQ_TOKEN:
        raise HTTPException(500, "LOGSEQ_TOKEN not configured in .env")
    return LogseqClient(LOGSEQ_TOKEN, LOGSEQ_URL)


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health():
    client = get_client()
    connected = await client.ping()
    return {"status": "ok" if connected else "error", "logseq_url": LOGSEQ_URL, "connected": connected}


@app.post("/import")
async def import_file(
    file: UploadFile = File(...),
    overwrite: bool = Query(False, description="Replace page if it already exists"),
    filename_as_title: bool = Query(False, description="Force filename (without .md) as page title"),
    tags: str = Query("", description="Page tags value, e.g. 'trabajo'"),
):
    if not file.filename or not file.filename.lower().endswith(".md"):
        raise HTTPException(400, "Only .md files are supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be UTF-8 encoded")

    parsed_title, blocks = parse_markdown(text)
    title = Path(file.filename).stem if filename_as_title or not parsed_title else parsed_title

    client = get_client()

    existing = await client.get_page(title)
    if existing and not overwrite:
        raise HTTPException(
            409,
            {
                "error": "page_exists",
                "message": f"La página '{title}' ya existe en Logseq.",
                "page": title,
            },
        )

    if existing and overwrite:
        await client.delete_page(title)

    inserted = 0
    errors = []

    if tags.strip():
        try:
            await client.append_block(title, f"tags:: {tags.strip()}")
            inserted += 1
        except Exception as err:
            errors.append(f"tags property: {err}")

    for block in blocks:
        try:
            parent = await client.append_block(title, block.content)
            parent_uuid = _extract_uuid(parent)
            inserted += 1
            if block.children and parent_uuid:
                n, errs = await _insert_children(client, parent_uuid, block.children)
                inserted += n
                errors.extend(errs)
        except Exception as err:
            errors.append(str(err))

    return {
        "status": "ok",
        "page": title,
        "blocks_inserted": inserted,
        "errors": errors,
    }


async def _insert_children(client: LogseqClient, parent_uuid: str, children: list) -> tuple[int, list]:
    inserted = 0
    errors = []
    for child in children:
        try:
            result = await client.insert_child_block(parent_uuid, child.content)
            child_uuid = _extract_uuid(result)
            inserted += 1
            if child.children and child_uuid:
                n, errs = await _insert_children(client, child_uuid, child.children)
                inserted += n
                errors.extend(errs)
        except Exception as err:
            errors.append(str(err))
    return inserted, errors


def _extract_uuid(block: dict) -> str:
    """Handles both flat {uuid: ...} and nested {data: {uuid: ...}} responses."""
    if isinstance(block, dict):
        if "uuid" in block:
            return block["uuid"]
        if "data" in block and isinstance(block["data"], dict):
            return block["data"].get("uuid", "")
    return ""
