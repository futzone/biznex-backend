from typing import List, Type

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.user import AdminUser
from app.api.schemas.user import AdminCreateRequest
from app.core.databases.postgres import get_general_session
from app.core.models.base import Base
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select

router = APIRouter()


def get_all_models(base: Type[Base]) -> List[Type[Base]]:
    """
    Returns all SQLAlchemy models that inherit from the given Base class.
    """
    return base.__subclasses__() + [
        subclass
        for child in base.__subclasses__()
        for subclass in get_all_models(child)
    ]


# Function to get model names and table names
def get_model_info(base: Type[Base]) -> List[dict]:
    models = get_all_models(base)
    return [model.__tablename__ for model in models]


@router.get("/models")
async def get_models():
    return get_model_info(Base)


@router.post("/create-admin")
async def create_global_admin(
    admin: AdminCreateRequest, db: AsyncSession = Depends(get_general_session)
):
    # Phone numberni tekshirib ko'rish (agar kerak bo'lsa)
    result = await db.execute(
        select(AdminUser).filter(AdminUser.phone_number == admin.phone_number)
    )
    existing_admin = result.scalar_one_or_none()
    if existing_admin:
        raise HTTPException(
            status_code=400, detail="User with this phone number already exists"
        )

    # Parolni xashlash
    hashed_password = bcrypt.hashpw(admin.password.encode("utf-8"), bcrypt.gensalt())

    # Global admin yaratish
    new_admin = AdminUser(
        full_name="Global Admin",
        phone_number=admin.phone_number,
        password=hashed_password.decode("utf-8"),
        is_global_admin=True,
    )

    # Ma'lumotlar bazasiga kiritish
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)

    return {
        "message": "Global admin created successfully",
        "admin": new_admin.phone_number,
    }
