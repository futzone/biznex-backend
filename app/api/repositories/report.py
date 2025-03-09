from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.models.report import Report
from app.api.schemas.report import ReportCreate, ReportUpdate
from app.core.databases.postgres import get_general_session

from sqlalchemy.exc import SQLAlchemyError


class ReportRepository:
    def __init__(self, session: AsyncSession = Depends(get_general_session)):
        self.session = session

    async def create_report(self, report_create: ReportCreate) -> Report:
        try:
            new_report = Report(**report_create.dict())
            self.session.add(new_report)
            await self.session.commit()
            await self.session.refresh(new_report)
            return new_report
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise

    async def get_all_reports(self, skip: int = 0, limit: int = 10) -> list[Report]:
        try:
            result = await self.session.execute(
                select(Report).offset(skip).limit(limit)
            )
            return result.scalars().all()

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise

    async def get_report_by_id(self, report_id: int) -> Report:
        try:
            result = await self.session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalars().first()
            if not report:
                raise ValueError(f"Report with id {report_id} not found")
            return report
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise

    async def update_report(self, report_id: int, report_data: ReportUpdate) -> Report:
        report = await self.get_report_by_id(report_id)
        if not report:
            return None

        for key, value in report_data.dict(exclude_unset=True).items():
            setattr(report, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(report)
            return report
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def delete_report(self, report_id: int) -> dict:
        report = await self.get_report_by_id(report_id)
        if not report:
            return False

        try:
            await self.session.delete(report)
            await self.session.commit()
            return {"detail": "Report successfully deleted"}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
