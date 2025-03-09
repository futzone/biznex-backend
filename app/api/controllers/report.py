from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.repositories.report import ReportRepository
from app.api.schemas.report import ReportCreate, ReportUpdate


class ReportController:
    @staticmethod
    async def create_report(report_data: ReportCreate, session: AsyncSession):
        report_repo = ReportRepository(session)
        new_report = await report_repo.create_report(report_data)
        return new_report

    @staticmethod
    async def get_report_by_id(report_id: int, session: AsyncSession):
        report_repo = ReportRepository(session)
        report = await report_repo.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )
        return report

    @staticmethod
    async def get_all_reports(session: AsyncSession, skip: int, limit: int):
        report_repo = ReportRepository(session)
        reports = await report_repo.get_all_reports(skip, limit)
        return reports

    @staticmethod
    async def update_report(
        report_id: int, report_data: ReportUpdate, session: AsyncSession
    ):
        report_repo = ReportRepository(session)
        updated_report = await report_repo.update_report(report_id, report_data)
        if not updated_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )
        return updated_report

    @staticmethod
    async def delete_report(report_id: int, session: AsyncSession):
        report_repo = ReportRepository(session)
        success = await report_repo.delete_report(report_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )
        return {"detail": "Report successfully deleted"}
