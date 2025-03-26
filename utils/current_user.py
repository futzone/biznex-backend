from starlette.requests import Request

from app.api.controllers.user import UserController
from app.api.utils.user import AuthUtils


async def current_user(request: Request, controller: UserController):
    token = await AuthUtils.get_current_user_from_cookie(request)
    return await controller.get_current_user(token=token)
