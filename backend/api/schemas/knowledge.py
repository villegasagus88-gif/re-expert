"""
Knowledge file schemas.
"""
from pydantic import BaseModel


class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    content_type: str
    created_at: str = ""
    updated_at: str = ""


class FileUploadResponse(BaseModel):
    path: str
    size: int
    content_type: str
    public_url: str


class CacheClearResponse(BaseModel):
    cleared: int
    message: str
