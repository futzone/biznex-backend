# app/api/controllers/file_controller.py
import base64
from fastapi import HTTPException
from pathlib import Path
from fastapi.responses import FileResponse
from app.api.repositories.file import FileRepository

upload_dir = Path("fast_trendify/media")


class FileController:
    def __init__(self, repository: FileRepository):
        self.__repository = repository

    async def upload_file(self, filepath: str, base64_image: str) -> dict:
        try:
            if ";base64," in base64_image:
                base64_image = base64_image.split(";base64,")[1]

            file_content = base64.b64decode(base64_image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data {str(e)}")

        try:
            filepath = await self.__repository.save_file(file_content, filepath)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

        return {
            "filepath": filepath,
        }

    async def download_file(self, file_path: str):
        filepath = upload_dir / file_path

        if not filepath.exists():
            raise HTTPException(404, detail=f"File not found: {filepath}")

        media_type = "application/octet-stream"
        if filepath.suffix in [".png", ".jpg", ".jpeg"]:
            media_type = "image/png" if filepath.suffix == ".png" else "image/jpeg"

        return FileResponse(filepath, media_type=media_type, filename=filepath.name)
