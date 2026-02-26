import uuid
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
import aiofiles

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain",
    "application/zip",
}


@router.post("/upload", response_model=AttachmentResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    post_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    url = f"/uploads/{stored_filename}"

    attachment = Attachment(
        post_id=post_id,
        uploader_id=current_user.user_id,
        filename=file.filename,
        stored_filename=stored_filename,
        content_type=file.content_type,
        file_size=len(content),
        url=url,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)
    return attachment
