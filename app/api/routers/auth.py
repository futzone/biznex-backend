from typing import Optional
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    File,
    UploadFile,
    Form,
    status,
)
from sqlalchemy.orm import Session

from app.api.models.user import User
from app.core.databases.postgres import get_general_session
from app.api.controllers.auth import AuthController
from app.api.schemas.user import RefreshTokenRequest
from app.api.utils.user import AuthUtils
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register")
async def register_user(
    full_name: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_general_session),
):
    image_path = None
    if profile_picture:
        unique_filename = f"{uuid.uuid4()}_{profile_picture.filename}"
        image_path = f"media/profile_picture/{unique_filename}".replace(" ", "_")

        try:
            with open(image_path, "wb") as buffer:
                contents = await profile_picture.read()
                buffer.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image: {str(e)}",
            )
    if image_path == None:
        image_path = ""

    return await AuthController.register_user(
        full_name=full_name,
        phone_number=phone_number,
        password=password,
        profile_picture=image_path,
        db=db,
    )


@router.post("/verify-sms")
async def verify_sms(
    phone_number: str, code: str, db: Session = Depends(get_general_session)
):
    return await AuthController.verify_sms_code(
        phone_number=phone_number, code=code, db=db
    )


@router.post("/login")
async def login_user(
    phone_number: str,
    password: str,
    response: Response,
    db: Session = Depends(get_general_session),
):
    return await AuthController.login_user(
        phone_number=phone_number, password=password, response=response, db=db
    )


@router.put("/update-password")
async def update_password(
    request: Request,  # Request ni boshida ko'rsatish
    old_password: str = Form(...),  # Form parametrlari oxirida bo'lishi kerak
    new_password: str = Form(...),
    controller: AuthController = Depends(),
    session: AsyncSession = Depends(get_general_session),
):
    current_user = await controller.get_current_user(
        request=request,
        session=session,
    )
    return await controller.update_password(
        old_password=old_password,
        new_password=new_password,
        current_user=current_user,
        db=session,
    )


@router.post("/refresh-token")
async def refresh_access_token(
    token_request: RefreshTokenRequest,  # Accept as string, which is more typical for tokens
    response: Response,
):

    refresh_token = token_request.refresh_token

    if refresh_token:
        return await AuthController.refresh_token(
            refresh_token.encode(), response
        )  # Convert to bytes before passing
    else:
        raise HTTPException(status_code=400, detail="Invalid refresh token format")


@router.post("/forgot-password")
async def forgot_password(
    phone_number: str, db: Session = Depends(get_general_session)
):
    return await AuthController.forgot_password(
        phone_number=phone_number, response=Response(), db=db
    )


@router.post("/verify-reset-code")
async def verify_reset_code(
    phone_number: str, code: str, db: Session = Depends(get_general_session)
):
    return await AuthController.verify_reset_code(
        phone_number=phone_number, code=code, db=db
    )


@router.post("/reset-password")
async def reset_password(
    reset_token: str, new_password: str, db: Session = Depends(get_general_session)
):
    return await AuthController.reset_password(
        reset_token=reset_token, new_password=new_password, response=Response(), db=db
    )
