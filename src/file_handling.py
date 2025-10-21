from typing import List
from fastapi import File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from src.api.db.schema import DocResponse, DocBase
import os

ALLOWED_EXTENSIONS = {
    "pdf":"application/pdf",
    "txt":"text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}

MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")

async def store_file(files: List[UploadFile] = File(...)) -> List[DocBase]:
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    documents: List[DocBase] = []
    
    for file in files:
            
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types:{', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        
        content = await file.read()

        if len(content)> MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        save_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(save_path, "wb") as f:
            f.write(content)

        documents.append(
            DocBase(
                filename= file.filename,
                file_type= file.content_type,
                file_size= len(content),
                file_path= save_path
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

