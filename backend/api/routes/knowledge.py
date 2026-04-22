"""
Knowledge base file management routes.
"""
from api.schemas.knowledge import CacheClearResponse, FileInfo, FileUploadResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from models.user import User
from services.knowledge_storage import knowledge_storage

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".docx", ".xlsx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get(
    "/files",
    response_model=list[FileInfo],
    summary="Listar archivos del knowledge base",
)
async def list_files(
    folder: str = Query("", description="Subcarpeta (vacio = raiz)"),
    _user: User = Depends(get_current_user),
):
    return await knowledge_storage.list_files(folder)


@router.get(
    "/files/{path:path}",
    summary="Descargar un archivo",
)
async def get_file(
    path: str,
    _user: User = Depends(get_current_user),
):
    content, content_type = await knowledge_storage.get_file(path)
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{path.split("/")[-1]}"'},
    )


@router.post(
    "/files/{path:path}",
    response_model=FileUploadResponse,
    status_code=201,
    summary="Subir archivo al knowledge base",
)
async def upload_file(
    path: str,
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    # Validate extension
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension no permitida. Permitidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Maximo: {MAX_FILE_SIZE // (1024*1024)}MB",
        )
    # Reset file position after reading
    await file.seek(0)

    return await knowledge_storage.upload_file(path, file)


@router.delete(
    "/files/{path:path}",
    status_code=204,
    summary="Eliminar archivo del knowledge base",
)
async def delete_file(
    path: str,
    _user: User = Depends(get_current_user),
):
    await knowledge_storage.delete_file(path)


@router.delete(
    "/cache",
    response_model=CacheClearResponse,
    summary="Limpiar cache de archivos",
)
async def clear_cache(
    _user: User = Depends(get_current_user),
):
    count = knowledge_storage.clear_cache()
    return CacheClearResponse(cleared=count, message=f"{count} archivos removidos del cache")
