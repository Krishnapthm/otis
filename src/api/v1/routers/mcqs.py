import json
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.db.models.session import get_db
from src.api.crud import create_mcq, get_all_mcqs, get_mcq
from src.api.db.schema import AuthResponse, CreateMCQ, ReadMCQ
from typing import List
import uuid
from src.core.security import get_current_user
from src.services.utils.export_utils import (
    build_export_filename,
    format_mcq_as_docx,
    format_mcq_as_json,
    format_mcq_as_markdown,
    format_mcq_as_pdf,
    shape_mcq_for_mode,
)

router = APIRouter(prefix="/mcqs")
legacy_router = APIRouter(prefix="/mcq")


class MCQExportFormat(str, Enum):
    md = "md"
    json = "json"
    pdf = "pdf"
    docx = "docx"


class MCQExportMode(str, Enum):
    raw = "raw"
    test = "test"


@router.post(
    "/", name="create MCQ", response_model=ReadMCQ, status_code=status.HTTP_201_CREATED
)
@legacy_router.post(
    "/create",
    name="create MCQ (legacy)",
    response_model=ReadMCQ,
    status_code=status.HTTP_201_CREATED,
)
async def create_mcq_endpoint(
    mcqs: CreateMCQ,
    db: AsyncSession = Depends(get_db),
    _current_user: AuthResponse = Depends(get_current_user),
):
    new_mcq = await create_mcq(db, mcqs)
    return new_mcq


@router.get("/", name="list mcq", response_model=List[ReadMCQ])
@legacy_router.get("/list", name="list mcq (legacy)", response_model=List[ReadMCQ])
async def list_mcq(
    db: AsyncSession = Depends(get_db),
    _current_user: AuthResponse = Depends(get_current_user),
) -> List[ReadMCQ]:
    mcqs = await get_all_mcqs(db)
    return mcqs


# @router.get("/list/{project_id}", name='list mcq', response_model=List[ReadMCQ])
# async def list_mcq(project_id: uuid, db: AsyncSession = Depends(get_db))-> List[ReadMCQ]:
#     mcqs = await get_mcq(db, project_id)
#     return mcqs


@router.get("/download/{id}", name="donwload mcq")
@legacy_router.get("/download/{id}", name="download mcq (legacy)")
async def download_mcq(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: AuthResponse = Depends(get_current_user),
):
    mcqs = await get_mcq(db, id)

    if not mcqs:
        return Response(status_code=404, content="MCQ not found")

    json_data = [mcq.model_dump() for mcq in mcqs]

    json_bytes = json.dumps(json_data, indent=2, default=str).encode("utf-8")

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="mcqs_{id}.json"'},
    )


@router.get("/{mcq_id}/export", name="export mcq")
@legacy_router.get("/{mcq_id}/export", name="export mcq (legacy)")
async def export_mcq(
    mcq_id: uuid.UUID,
    format: MCQExportFormat,
    mode: MCQExportMode,
    db: AsyncSession = Depends(get_db),
    _current_user: AuthResponse = Depends(get_current_user),
):
    mcqs = await get_mcq(db, mcq_id)
    if not mcqs:
        raise HTTPException(status_code=404, detail="MCQ not found")

    mcq_payload = mcqs[0].mcq.model_dump(mode="json")
    shaped_payload = shape_mcq_for_mode(mcq_payload, mode.value)

    formatter_map = {
        MCQExportFormat.md: format_mcq_as_markdown,
        MCQExportFormat.json: format_mcq_as_json,
        MCQExportFormat.pdf: format_mcq_as_pdf,
        MCQExportFormat.docx: format_mcq_as_docx,
    }
    media_type_map = {
        MCQExportFormat.md: "text/markdown; charset=utf-8",
        MCQExportFormat.json: "application/json",
        MCQExportFormat.pdf: "application/pdf",
        MCQExportFormat.docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    formatter = formatter_map[format]
    content = formatter(shaped_payload, mode.value)
    filename = build_export_filename(mode.value, format.value)

    return Response(
        content=content,
        media_type=media_type_map[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@legacy_router.get(
    "/list/{id}", name="list mcq by id (legacy)", response_model=List[ReadMCQ]
)
async def list_mcq_by_id_legacy(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: AuthResponse = Depends(get_current_user),
) -> List[ReadMCQ]:
    mcqs = await get_mcq(db, id)
    return mcqs or []
