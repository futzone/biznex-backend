# app/api/repositories/file_repository.py
import os
import uuid
from typing import Tuple


class FileRepository:
    def __init__(self, upload_dir: str = "media"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def save_file(self, file_content: bytes, filepath: str) -> str:
        file_ext = os.path.splitext(filepath)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}.jpg"
        filepath = os.path.join(self.upload_dir, filepath, unique_filename)

        with open(filepath, "wb") as f:
            f.write(file_content)
        filepath = filepath.replace("\\", "/")

        return filepath
