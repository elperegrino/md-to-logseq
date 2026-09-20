import asyncio
import httpx
from typing import Optional

# Logseq's HTTP API is single-threaded; serialize all calls globally.
_api_sem = asyncio.Semaphore(1)


class LogseqClient:
    def __init__(self, token: str, base_url: str = "http://127.0.0.1:12315"):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _call(self, method: str, args: list) -> dict:
        async with _api_sem:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api",
                    json={"method": method, "args": args},
                    headers=self.headers,
                )
        response.raise_for_status()
        return response.json()

    async def ping(self) -> bool:
        try:
            await self._call("logseq.App.getUserConfigs", [])
            return True
        except Exception:
            return False

    async def get_page(self, name: str) -> Optional[dict]:
        try:
            result = await self._call("logseq.Editor.getPage", [name])
            return result if result else None
        except Exception:
            return None

    async def create_page(self, name: str) -> dict:
        return await self._call(
            "logseq.Editor.createPage",
            [name, {}, {"createFirstBlock": False, "redirect": False}],
        )

    async def append_block(self, page_name: str, content: str) -> dict:
        """Appends a top-level block to a page. Returns block with uuid."""
        return await self._call("logseq.Editor.appendBlockInPage", [page_name, content])

    async def insert_child_block(self, parent_uuid: str, content: str) -> dict:
        """Inserts content as a child of parent_uuid."""
        return await self._call(
            "logseq.Editor.insertBlock",
            [parent_uuid, content, {"before": False, "sibling": False}],
        )

    async def delete_page(self, name: str) -> bool:
        try:
            await self._call("logseq.Editor.deletePage", [name])
            return True
        except Exception:
            return False

    async def insert_sibling_block(self, ref_uuid: str, content: str) -> dict:
        """Inserts content as a sibling after ref_uuid."""
        return await self._call(
            "logseq.Editor.insertBlock",
            [ref_uuid, content, {"before": False, "sibling": True}],
        )
