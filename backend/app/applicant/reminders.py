"""US7: opted-in, verified applicants; official dates only, at 7, 1 and 0 days."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.applicant import mail
from app.applicant.models import Applicant, DeadlineReminder, SavedProgram
from app.applicant.service import now, saved_checklist
from app.catalogue.models import Program
from app.config import Settings
from app.db import get_session

logger = logging.getLogger(__name__)

_TEXT = {
    "en": (
        "SDU application deadline reminder",
        "Application deadline",
        "Documents still to prepare",
        "All listed documents are prepared.",
        "The document list is not published. Contact the admissions office.",
        "Manage your checklist or turn off reminders",
    ),
    "ru": (
        "SDU: напоминание о сроке подачи",
        "Срок подачи заявления",
        "Осталось подготовить",
        "Все документы из списка подготовлены.",
        "Список документов не опубликован. Обратитесь в приёмную комиссию.",
        "Список документов и отключение напоминаний",
    ),
    "kk": (
        "SDU: өтініш мерзімі туралы еске салу",
        "Өтініш беру мерзімі",
        "Дайындалуы керек құжаттар",
        "Тізімдегі барлық құжат дайын.",
        "Құжаттар тізімі жарияланбаған. Қабылдау комиссиясына хабарласыңыз.",
        "Құжаттар тізімі және еске салуларды өшіру",
    ),
}


def send_due_reminders(session: Session, settings: Settings, today: date | None = None) -> int:
    if not settings.applicant_accounts_enabled or not settings.smtp_host:
        return 0
    today = today or datetime.now(ZoneInfo("Asia/Almaty")).date()
    saved_keys = session.execute(
        select(SavedProgram.applicant_id, SavedProgram.program_id, SavedProgram.applicant_type)
    ).all()
    sent = 0
    for user_id, program_id, applicant_type in saved_keys:
        # Re-read preferences for each delivery, so opting out stops future messages.
        user = session.get(Applicant, user_id, populate_existing=True)
        program = session.get(Program, program_id, populate_existing=True)
        if not user or not user.verified or not user.reminders_enabled or not program or not program.is_active:
            continue
        deadline = getattr(program, f"deadline_{applicant_type}")
        milestone = (deadline - today).days if deadline else -1
        if milestone not in (7, 1, 0):
            continue
        key = dict(
            applicant_id=user_id,
            program_id=program_id,
            applicant_type=applicant_type,
            deadline=deadline,
            milestone=milestone,
        )
        session.execute(insert(DeadlineReminder).values(**key).on_conflict_do_nothing())
        delivery = session.scalar(
            select(DeadlineReminder)
            .where(
                *(getattr(DeadlineReminder, field) == value for field, value in key.items()),
                DeadlineReminder.sent_at.is_(None),
            )
            .with_for_update(skip_locked=True)
        )
        if delivery is None:
            session.commit()
            continue
        checklist = saved_checklist(session, user, program_id, applicant_type, settings)
        subject, deadline_label, missing_label, complete, unavailable, manage = _TEXT[user.language]
        title = getattr(program, f"title_{user.language}", None) or program.title
        missing = "\n".join(f"- {item.name}" for item in checklist.items if not item.prepared)
        progress = unavailable if not checklist.items else f"{missing_label}:\n{missing}" if missing else complete
        body = (
            f"{title} ({program_id})\n{deadline_label}: {deadline.isoformat()}\n\n{progress}\n\n"
            f"{manage}: {settings.public_base_url.rstrip('/')}/account\n\n{settings.admissions_office_contact}\n"
        )
        try:
            mail.send_mail(settings, user.email, subject, body)
        except (OSError, smtplib.SMTPException):
            session.rollback()
            logger.warning("Reminder delivery failed; it will be retried on the next run.")
            continue
        delivery.sent_at = now()
        session.commit()
        sent += 1
    return sent


def _run(settings: Settings) -> None:
    with get_session(settings) as session:
        send_due_reminders(session, settings)


async def reminders_hourly(settings: Settings) -> None:
    while True:
        try:
            await asyncio.to_thread(_run, settings)
        except Exception:
            logger.exception("Reminder worker failed; retrying in one hour.")
        await asyncio.sleep(3600)
