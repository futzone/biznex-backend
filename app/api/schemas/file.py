from pydantic import BaseModel


class FileUploadRequest(BaseModel):
    filename: str
    base64_image: bytes


class FileUploadResponse(BaseModel):
    filepath: str


class FileDownloadRequest(BaseModel):
    filepath: str
