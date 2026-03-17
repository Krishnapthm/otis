from typing import List
import os
import tempfile
import shutil

from fastapi import File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from src.api.db.schema import DocResponse, DocBase
from src.core.hashing import compute_file_hash_streaming

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}

MAX_FILE_SIZE = 60 * 1024 * 1024  # 60MB

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")


async def store_file(files: List[UploadFile] = File(...)) -> List[DocBase]:
    """
    Store uploaded files with streaming hash computation.
    
    Memory-safe: streams file to disk first, then computes hash.
    This avoids loading full file into RAM for large PDFs.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    documents: List[DocBase] = []

    for file in files:
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}",
            )

        # Stream file to temp location (never loads full file into RAM)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Check file size from disk
        file_size = os.path.getsize(tmp_path)
        if file_size > MAX_FILE_SIZE:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB",
            )

        # Compute hash from disk (streaming, memory-safe)
        file_hash = compute_file_hash_streaming(tmp_path)

        # Move to final location
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        shutil.move(tmp_path, save_path)

        documents.append(
            DocBase(
                filename=file.filename,
                file_type=file.content_type,
                file_size=file_size,
                file_path=save_path,
                file_hash=file_hash,
            )
        )

    return documents


async def delete_file(filename: str)-> bool:

    file_path  = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"{filename} does not exist")
    
    os.remove(file_path)

    return True

def download_file(filename: str)-> FileResponse:

    file_path  = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"{filename} does not exist")
    
    file_ext = filename.split(".")[-1].lower()
    media_type = ALLOWED_EXTENSIONS.get(file_ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
async def zip_files(filenames: List[str]):
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in filenames:
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=filename)
    
    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=documents.zip"}
    )

