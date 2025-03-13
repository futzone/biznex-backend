# app/api/routers/file.py
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import Response

from app.api.controllers.file import FileController
from app.api.repositories.file import FileRepository
from app.api.schemas.file import (
    FileDownloadRequest,
    FileUploadRequest,
    FileUploadResponse,
)
from utils.receipt_utils import ReceiptData, ReceiptStyle, generate_receipt

router = APIRouter()


def get_file_controller() -> FileController:
    return FileController(FileRepository())


@router.post("/upload-file/", response_model=FileUploadResponse)
async def upload_file(
    filepath: str = Form(...),
    base64_image: str = Form(...),
    controller: FileController = Depends(get_file_controller),
):

    return await controller.upload_file(filepath, base64_image)


@router.get("/get-file/", response_model=FileUploadResponse)
async def get_file(
    request: Request,
    controller: FileController = Depends(get_file_controller),
):
    filepath = request.headers.get("filepath")
    return await controller.download_file(filepath)


@router.post("/printing/generate")
async def create_receipt(data: ReceiptData, style: ReceiptStyle):
    return Response(content="")
