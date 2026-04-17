"""
KnowledgeStorageService - manages files in Supabase Storage.

Bucket: 'knowledge'
Supports: list, get, upload, delete files.
Includes in-memory cache with TTL to avoid repeated downloads.
"""
import time
from dataclasses import dataclass, field

import httpx
from fastapi import HTTPException, UploadFile, status

from config.settings import settings

STORAGE_URL = f"{settings.SUPABASE_URL}/storage/v1"
HEADERS = {
    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
}
BUCKET = "knowledge"


@dataclass
class CachedFile:
    content: bytes
    content_type: str
    cached_at: float


@dataclass
class KnowledgeStorageService:
    """
    Manages knowledge base files in Supabase Storage.
    Uses service_role key to bypass RLS (knowledge is shared across users).
    """

    _cache: dict[str, CachedFile] = field(default_factory=dict)
    _cache_ttl: int = 300  # 5 minutes

    def _is_cached(self, path: str) -> bool:
        if path not in self._cache:
            return False
        return (time.time() - self._cache[path].cached_at) < self._cache_ttl

    async def list_files(self, folder: str = "") -> list[dict]:
        """
        List files in the knowledge bucket.

        Args:
            folder: subfolder path (empty = root)

        Returns:
            List of file objects with name, size, created_at, etc.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{STORAGE_URL}/object/list/{BUCKET}",
                headers={**HEADERS, "Content-Type": "application/json"},
                json={
                    "prefix": folder,
                    "limit": 1000,
                    "offset": 0,
                    "sortBy": {"column": "name", "order": "asc"},
                },
            )

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error listando archivos: {resp.text}",
                )

            items = resp.json()
            # Filter out folder placeholders (items with null metadata)
            return [
                {
                    "name": item["name"],
                    "path": f"{folder}/{item['name']}".strip("/"),
                    "size": item.get("metadata", {}).get("size", 0) if item.get("metadata") else 0,
                    "content_type": item.get("metadata", {}).get("mimetype", "") if item.get("metadata") else "",
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                }
                for item in items
                if item.get("id") is not None  # skip folder entries
            ]

    async def get_file(self, path: str) -> tuple[bytes, str]:
        """
        Download a file from the knowledge bucket.
        Returns (content_bytes, content_type). Uses cache if available.

        Args:
            path: file path within the bucket (e.g. "docs/guide.pdf")
        """
        if self._is_cached(path):
            cached = self._cache[path]
            return cached.content, cached.content_type

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{STORAGE_URL}/object/{BUCKET}/{path}",
                headers=HEADERS,
            )

            if resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archivo no encontrado: {path}",
                )

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error descargando archivo: {resp.text}",
                )

            content_type = resp.headers.get("content-type", "application/octet-stream")

            # Cache the file
            self._cache[path] = CachedFile(
                content=resp.content,
                content_type=content_type,
                cached_at=time.time(),
            )

            return resp.content, content_type

    async def upload_file(self, path: str, file: UploadFile) -> dict:
        """
        Upload a file to the knowledge bucket.

        Args:
            path: destination path (e.g. "docs/guide.pdf")
            file: FastAPI UploadFile

        Returns:
            Dict with path and public URL.
        """
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{STORAGE_URL}/object/{BUCKET}/{path}",
                headers={
                    **HEADERS,
                    "Content-Type": content_type,
                    "x-upsert": "true",  # overwrite if exists
                },
                content=content,
            )

            if resp.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error subiendo archivo: {resp.text}",
                )

            # Invalidate cache for this path
            self._cache.pop(path, None)

            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"

            return {
                "path": path,
                "size": len(content),
                "content_type": content_type,
                "public_url": public_url,
            }

    async def delete_file(self, path: str) -> None:
        """Delete a file from the knowledge bucket."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{STORAGE_URL}/object/{BUCKET}/{path}",
                headers=HEADERS,
            )

            if resp.status_code not in (200, 204):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error eliminando archivo: {resp.text}",
                )

            self._cache.pop(path, None)

    async def get_text_content(self, path: str) -> str:
        """
        Download and decode a text file (md, txt, csv).
        Useful for feeding knowledge to the AI.
        """
        content, content_type = await self.get_file(path)
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo {path} no es un archivo de texto valido",
            )

    def clear_cache(self) -> int:
        """Clear all cached files. Returns count of cleared items."""
        count = len(self._cache)
        self._cache.clear()
        return count


# Singleton instance
knowledge_storage = KnowledgeStorageService()
