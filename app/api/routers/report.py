from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.models.user import AdminUser
from app.api.routers.admin import get_current_admin_user
from app.core.databases.postgres import get_general_session
from app.api.controllers.report import ReportController
from app.api.schemas.report import ReportCreate
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/")
async def get_report(
    skip: int,
    limit: int,
    session: AsyncSession = Depends(get_general_session),
    controller: ReportController = Depends(),
):
    report = await controller.get_all_reports(session, skip=skip, limit=limit)
    return report


@router.post("/")
async def create_report(
    session: Session = Depends(get_general_session),
    controller: ReportController = Depends(),
    report_create: ReportCreate = Depends(),
):
    report = await controller.create_report(report_create, session)
    return report


@router.get("/{report_id}")
async def get_report_by_id(
    report_id: int,
    session: Session = Depends(get_general_session),
    controller: ReportController = Depends(),
):
    report = await controller.get_report_by_id(report_id, session)
    return report


@router.delete("/")
async def delete_report(
    report_id: int,
    session: Session = Depends(get_general_session),
    controller: ReportController = Depends(),
):

    report = await controller.delete_report(report_id, session)
    return report
