from dataclasses import field
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RatingPictureResponseSchema(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True


class RatingCreateSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)  # 1..5
    comment: str
    user_id: int
    product_id: int


class RatingUpdateSchema(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class RatingResponseSchema(BaseModel):
    id: int
    rating: int
    comment: str
    user_id: int
    product_id: int
    pictures: List[RatingPictureResponseSchema] = field(default_factory=list)

    class Config:
        from_attributes = True

class ReviewSampleResponse(BaseModel):
    user_name: str
    user_avatar: Optional[str] = None
    rating: int
    comment: str  # Assuming JSONB field for multilingual comments
    images: List[str] = []

class ProductRatingStatsResponse(BaseModel):
    average_rating: float
    total_ratings: int
    rating_distribution: Dict[int, int]  # {1: count, 2: count, ...}
    percentage_score: int  # 0-100%
    sample_reviews: List[ReviewSampleResponse] = []