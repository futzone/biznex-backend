from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.controllers.revision import RevisionController
from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.api.schemas.revision import CreateRevisionSchema, RevisionDetailResponse, RevisionItemCreate, RevisionItemResponse, RevisionResponse
from app.core.databases.postgres import get_general_session

router = APIRouter()


@router.get("/", response_model=Optional[RevisionResponse])
async def get_active_revision(
        request: Request,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    warehouse_id = int(request.headers.get('id'))
    revision = await controller.get_active_revision(warehouse_id)
    if revision is None:
        raise HTTPException(
            status_code=404,
            detail="No active revision found for this warehouse"
        )
    return revision


@router.post("/", response_model=RevisionResponse)
async def create_revision(
        schema: CreateRevisionSchema,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    return await controller.create_revision(schema, current_user.id)


@router.get("/{revision_id}", response_model=RevisionDetailResponse)
async def get_revision_detail(
        revision_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    revision = await controller.get_revision_detail(revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail="Revision not found")
    return revision


@router.post("/{revision_id}/items", response_model=RevisionItemResponse)
async def add_revision_item(
        request: Request,
        revision_id: int,
        schema: RevisionItemCreate,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    warehouse_id = int(request.headers.get('id'))
    return await controller.add_revision_item(revision_id, schema, warehouse_id)


@router.post("/{revision_id}/complete", response_model=RevisionResponse)
async def complete_revision(
        revision_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    return await controller.complete_revision(revision_id, current_user.id)


@router.post("/{revision_id}/cancel", response_model=RevisionResponse)
async def cancel_revision(
        revision_id: int,
        session: AsyncSession = Depends(get_general_session),
        current_user: AdminUser = Depends(get_current_admin_user),
):
    controller = RevisionController(session)
    return await controller.cancel_revision(revision_id, current_user.id)
