from typing import Optional

from pydantic import BaseModel


class PaginationModel(BaseModel):
    limit: Optional[int] = 10
    offset: Optional[int] = 0
    status: Optional[str] = None
