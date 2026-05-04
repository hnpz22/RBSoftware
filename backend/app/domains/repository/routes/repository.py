from __future__ import annotations

import os
import uuid as uuid_module
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session, or_, select

from app.core.database import get_session
from app.core.permissions import require_roles
from app.core.storage import storage_service
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.repository.models.repository_file import RepositoryFile
from app.domains.repository.models.repository_folder import RepositoryFolder

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg",
    ".gif", ".mp4", ".mov", ".avi",
}

# ── Schemas ───────────────────────────────────────────────────────────────────

class FolderRead(BaseModel):
    public_id: str
    name: str
    description: str | None
    parent_id: str | None
    subfolder_count: int
    file_count: int
    created_by_name: str | None
    created_at: datetime
    updated_at: datetime

class FolderCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None

class FolderUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class FileRead(BaseModel):
    public_id: str
    folder_id: str | None
    name: str
    description: str | None
    file_name: str
    file_size: int | None
    file_type: str | None
    uploaded_by_name: str | None
    created_at: datetime

class BreadcrumbItem(BaseModel):
    public_id: str
    name: str

class FolderDetail(BaseModel):
    public_id: str
    name: str
    description: str | None
    parent_id: str | None
    breadcrumb: list[BreadcrumbItem]
    subfolders: list[FolderRead]
    files: list[FileRead]
    created_by_name: str | None
    created_at: datetime
    updated_at: datetime

# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_name(user_id: int | None, session: Session) -> str | None:
    if user_id is None:
        return None
    u = session.get(User, user_id)
    return f"{u.first_name} {u.last_name}" if u else None

def _parent_public_id(parent_id: int | None, session: Session) -> str | None:
    if parent_id is None:
        return None
    parent = session.get(RepositoryFolder, parent_id)
    return parent.public_id if parent else None

def _folder_read(folder: RepositoryFolder, session: Session) -> FolderRead:
    subfolder_count = len(
        session.exec(select(RepositoryFolder).where(RepositoryFolder.parent_id == folder.id)).all()
    )
    file_count = len(
        session.exec(select(RepositoryFile).where(RepositoryFile.folder_id == folder.id)).all()
    )
    return FolderRead(
        public_id=folder.public_id,
        name=folder.name,
        description=folder.description,
        parent_id=_parent_public_id(folder.parent_id, session),
        subfolder_count=subfolder_count,
        file_count=file_count,
        created_by_name=_user_name(folder.created_by, session),
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )

def _file_read(f: RepositoryFile, session: Session) -> FileRead:
    folder_public_id = None
    if f.folder_id:
        folder = session.get(RepositoryFolder, f.folder_id)
        folder_public_id = folder.public_id if folder else None
    return FileRead(
        public_id=f.public_id,
        folder_id=folder_public_id,
        name=f.name,
        description=f.description,
        file_name=f.file_name,
        file_size=f.file_size,
        file_type=f.file_type,
        uploaded_by_name=_user_name(f.uploaded_by, session),
        created_at=f.created_at,
    )

def _get_folder(session: Session, public_id: str) -> RepositoryFolder:
    folder = session.exec(
        select(RepositoryFolder).where(RepositoryFolder.public_id == public_id)
    ).first()
    if folder is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carpeta no encontrada")
    return folder

def _get_file(session: Session, public_id: str) -> RepositoryFile:
    f = session.exec(
        select(RepositoryFile).where(RepositoryFile.public_id == public_id)
    ).first()
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    return f

def _breadcrumb(folder: RepositoryFolder, session: Session) -> list[BreadcrumbItem]:
    crumbs: list[BreadcrumbItem] = []
    current: RepositoryFolder | None = folder
    while current is not None:
        crumbs.append(BreadcrumbItem(public_id=current.public_id, name=current.name))
        current = session.get(RepositoryFolder, current.parent_id) if current.parent_id else None
    crumbs.reverse()
    return crumbs

def _collect_file_keys(folder_id: int, session: Session) -> list[str]:
    keys = [
        f.file_key
        for f in session.exec(select(RepositoryFile).where(RepositoryFile.folder_id == folder_id)).all()
    ]
    for sub in session.exec(select(RepositoryFolder).where(RepositoryFolder.parent_id == folder_id)).all():
        keys.extend(_collect_file_keys(sub.id, session))
    return keys

# ── Folders ───────────────────────────────────────────────────────────────────

@router.get("/folders", response_model=list[FolderRead])
def list_root_folders(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    folders = session.exec(
        select(RepositoryFolder).where(RepositoryFolder.parent_id == None)  # noqa: E711
    ).all()
    return [_folder_read(f, session) for f in folders]


@router.get("/folders/{folder_id}", response_model=FolderDetail)
def get_folder(
    folder_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    folder = _get_folder(session, folder_id)
    subfolders = session.exec(
        select(RepositoryFolder).where(RepositoryFolder.parent_id == folder.id)
    ).all()
    files = session.exec(
        select(RepositoryFile).where(RepositoryFile.folder_id == folder.id)
    ).all()
    return FolderDetail(
        public_id=folder.public_id,
        name=folder.name,
        description=folder.description,
        parent_id=_parent_public_id(folder.parent_id, session),
        breadcrumb=_breadcrumb(folder, session),
        subfolders=[_folder_read(sf, session) for sf in subfolders],
        files=[_file_read(f, session) for f in files],
        created_by_name=_user_name(folder.created_by, session),
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


@router.post("/folders", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(
    data: FolderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    parent_id = None
    if data.parent_id:
        parent_id = _get_folder(session, data.parent_id).id
    now = datetime.now(timezone.utc)
    folder = RepositoryFolder(
        name=data.name,
        description=data.description,
        parent_id=parent_id,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(folder)
    session.commit()
    session.refresh(folder)
    return _folder_read(folder, session)


@router.patch("/folders/{folder_id}", response_model=FolderRead)
def update_folder(
    folder_id: str,
    data: FolderUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    folder = _get_folder(session, folder_id)
    if data.name is not None:
        folder.name = data.name
    if data.description is not None:
        folder.description = data.description
    folder.updated_at = datetime.now(timezone.utc)
    session.add(folder)
    session.commit()
    session.refresh(folder)
    return _folder_read(folder, session)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    folder = _get_folder(session, folder_id)
    for key in _collect_file_keys(folder.id, session):
        storage_service.delete_file(key)
    session.delete(folder)
    session.commit()

# ── Files ─────────────────────────────────────────────────────────────────────

@router.post("/files", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(default=None),
    folder_id: str | None = Form(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Extensión no permitida: {ext}. Permitidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    folder_db_id = None
    folder_segment = "root"
    if folder_id:
        folder = _get_folder(session, folder_id)
        folder_db_id = folder.id
        folder_segment = folder.public_id

    file_bytes = await file.read()
    key = f"repository/{folder_segment}/{uuid_module.uuid4()}{ext}"
    storage_service.upload_file(file_bytes, key, file.content_type or "application/octet-stream")

    now = datetime.now(timezone.utc)
    repo_file = RepositoryFile(
        folder_id=folder_db_id,
        name=name,
        description=description,
        file_key=key,
        file_name=file.filename or key.split("/")[-1],
        file_size=len(file_bytes),
        file_type=ext.lstrip(".") or None,
        uploaded_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    session.add(repo_file)
    session.commit()
    session.refresh(repo_file)
    return _file_read(repo_file, session)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    f = _get_file(session, file_id)
    storage_service.delete_file(f.file_key)
    session.delete(f)
    session.commit()


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    f = _get_file(session, file_id)
    url = storage_service.generate_presigned_url(f.file_key, expires_seconds=300, inline=False)
    return {"url": url, "file_name": f.file_name}


@router.get("/files/{file_id}/view")
def view_file(
    file_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    f = _get_file(session, file_id)
    url = storage_service.generate_presigned_url(f.file_key, expires_seconds=300, inline=True)
    return {"url": url, "file_name": f.file_name, "file_type": f.file_type}


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    like = f"%{q}%"
    folders = session.exec(
        select(RepositoryFolder).where(
            or_(RepositoryFolder.name.ilike(like), RepositoryFolder.description.ilike(like))
        )
    ).all()
    files = session.exec(
        select(RepositoryFile).where(
            or_(RepositoryFile.name.ilike(like), RepositoryFile.description.ilike(like))
        )
    ).all()
    return {
        "folders": [_folder_read(f, session) for f in folders],
        "files": [_file_read(f, session) for f in files],
    }
