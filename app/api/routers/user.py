import uuid
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from typing import List, Optional

from app.api.controllers.auth import AuthController
from app.api.schemas.user import SendFormticket, Sendticket, User, UserBase, UserCreate, UserResponse, UserUpdate
from app.api.controllers.user import UserController
from app.api.utils.user import AuthUtils
from app.core.databases.postgres import get_general_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[UserBase], status_code=status.HTTP_200_OK)
async def get_users(
    controller: UserController = Depends(), skip: int = 0, limit: int = 100
) -> List[User]:
    return await controller.get_all_users(skip, limit)


@router.get("/me", response_model=User, status_code=status.HTTP_200_OK)
async def get_current_user(request: Request, controller: UserController = Depends()):

    token = await AuthUtils.get_current_user_from_cookie(request)
    return await controller.get_current_user(token=token)


@router.get("/{user_id}", response_model=User, status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int, controller: UserController = Depends()) -> User:
    return await controller.get_user_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    request: Request,
    user_id: int,
    full_name: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_general_session),
):
    try:
        # Yangi rasmni saqlash
        image_path = None
        if profile_picture:
            # Yangi rasm uchun unikal nom yaratish
            unique_filename = f"{uuid.uuid4()}_{profile_picture.filename}"
            image_path = f"media/profile_picture/{unique_filename}".replace(" ", "_")

            # Rasmni saqlash
            try:
                with open(image_path, "wb") as buffer:
                    contents = await profile_picture.read()
                    buffer.write(contents)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving image: {str(e)}",
                )

        # Foydalanuvchini yangilash
        updated_user = await AuthController.update_user(
            user_id=user_id,
            full_name=full_name,
            profile_picture=image_path,
            db=db,
        )

        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, controller: UserController = Depends()):
    await controller.delete_user(user_id)
    return None



@router.post("/send-ticket", status_code=status.HTTP_201_CREATED)
async def send_ticket(
    data: Sendticket,
    controller: UserController = Depends(),
):
    return await controller.send_ticket(data)


@router.post("/send_form", status_code=status.HTTP_201_CREATED)
async def send_form(
    data: SendFormticket,
    controller: UserController = Depends(),
):
    return await controller.send_form(data)