"""US7: opted-in, verified applicants; official dates only, at 7, 1 and 0 days."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.errors import ApiProblem
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


_TYPE = {
    "en": {"local": "local applicants", "international": "international applicants"},
    "ru": {"local": "местные абитуриенты", "international": "иностранные абитуриенты"},
    "kk": {"local": "отандық талапкерлер", "international": "шетелдік талапкерлер"},
}
ALMATY = ZoneInfo("Asia/Almaty")


def _stage(days_left: int) -> int | None:
    """The latest milestone (7, 1 or 0 days) already reached.

    A milestone missed on its own day (outage, daily limit) is still sent on the following
    days until the next milestone replaces it; nothing is sent after the deadline.
    """
    if days_left < 0 or days_left > 7:
        return None
    return days_left if days_left in (0, 1) else 7


def _sent_last_24_hours(session: Session) -> int:
    """Reminder e-mails in the last 24 hours (Gmail counts a rolling day): one per applicant and send time."""
    sends = (
        select(DeadlineReminder.applicant_id, DeadlineReminder.sent_at)
        .where(DeadlineReminder.sent_at > now() - timedelta(hours=24))
        .distinct()
        .subquery()
    )
    return session.scalar(select(func.count()).select_from(sends)) or 0


def send_due_reminders(session: Session, settings: Settings, today: date | None = None) -> int:
    """Send one digest per applicant listing every saved checklist with a reminder due.

    Returns the number of e-mails sent. Every catalogue programme shares the same
    deadlines, so per-programme e-mails would arrive in bulk on the same three days.
    """
    if not settings.applicant_accounts_enabled or not settings.smtp_host:
        return 0
    today = today or datetime.now(ALMATY).date()
    due: dict[int, list[tuple[str, str, date, int]]] = defaultdict(list)
    for user_id, program_id, applicant_type in session.execute(
        select(SavedProgram.applicant_id, SavedProgram.program_id, SavedProgram.applicant_type)
    ).all():
        program = session.get(Program, program_id, populate_existing=True)
        if not program or not program.is_active:
            continue
        deadline = getattr(program, f"deadline_{applicant_type}")
        milestone = _stage((deadline - today).days) if deadline else None
        if milestone is not None:
            due[user_id].append((program_id, applicant_type, deadline, milestone))
    if not due:
        return 0
    remaining = settings.reminder_daily_limit - _sent_last_24_hours(session)
    # Closest deadline first; among equals (every programme shares its deadlines) whoever has
    # had the fewest and oldest reminders, so the daily limit does not always skip the same people.
    history = {
        user_id: (count, last)
        for user_id, count, last in session.execute(
            select(DeadlineReminder.applicant_id, func.count(), func.max(DeadlineReminder.sent_at))
            .where(DeadlineReminder.applicant_id.in_(due), DeadlineReminder.sent_at.is_not(None))
            .group_by(DeadlineReminder.applicant_id)
        )
    }
    never = datetime.min.replace(tzinfo=ALMATY)
    order = sorted(
        due,
        key=lambda user_id: (
            min(item[2] for item in due[user_id]),
            history.get(user_id, (0, never))[0],
            history.get(user_id, (0, never))[1],
            user_id,
        ),
    )
    sent = 0
    with mail.Mailer(settings) as mailer:
        for user_id in order:
            items = due[user_id]
            if sent >= remaining:
                logger.warning("Daily reminder limit reached; the remaining reminders are sent on later runs.")
                break
            try:
                sent += _send_digest(session, settings, mailer, user_id, items)
            except (OSError, smtplib.SMTPException) as error:
                session.rollback()
                logger.warning(
                    "Reminder delivery failed (%s); it will be retried on the next run.", mail.describe_error(error)
                )
                if mail.stops_batch(error):
                    break
            except Exception:
                # E.g. the applicant removed a checklist during the run: skip only this applicant.
                session.rollback()
                logger.exception("Reminder for one applicant failed; continuing with the others.")
    return sent


def _send_digest(
    session: Session, settings: Settings, mailer: mail.Mailer, user_id: int, items: list[tuple[str, str, date, int]]
) -> int:
    # Re-read preferences for each delivery, so opting out stops future messages.
    user = session.get(Applicant, user_id, populate_existing=True)
    if not user or not user.verified or not user.reminders_enabled:
        return 0
    subject, deadline_label, missing_label, complete, unavailable, manage = _TEXT[user.language]
    sections, deliveries = [], []
    for program_id, applicant_type, deadline, milestone in items:
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
            continue
        program = session.get(Program, program_id)
        try:
            checklist = saved_checklist(session, user, program_id, applicant_type, settings)
        except ApiProblem:
            continue  # removed from the account during this run
        title = getattr(program, f"title_{user.language}", None) or program.title
        missing = "\n".join(f"- {item.name}" for item in checklist.items if not item.prepared)
        progress = unavailable if not checklist.items else f"{missing_label}:\n{missing}" if missing else complete
        sections.append(
            f"{title} ({program_id}), {_TYPE[user.language][applicant_type]}\n"
            f"{deadline_label}: {deadline.isoformat()}\n\n{progress}"
        )
        deliveries.append(delivery)
    if not deliveries:
        session.commit()
        return 0
    body = (
        "\n\n".join(sections)
        + f"\n\n{manage}: {settings.public_base_url.rstrip('/')}/account\n\n{settings.admissions_office_contact}\n"
    )
    mailer.send(user.email, subject, body)
    sent_at = now()
    for delivery in deliveries:
        delivery.sent_at = sent_at
    session.commit()
    return 1


def _run(settings: Settings) -> None:
    from app.applicant.requests import send_request_notifications

    # Separate sessions: a reminder failure must not hold back reply notifications.
    for job in (send_due_reminders, send_request_notifications):
        try:
            with get_session(settings) as session:
                job(session, settings)
        except Exception:
            logger.exception("%s failed; retrying in one hour.", job.__name__)


async def reminders_hourly(settings: Settings) -> None:
    while True:
        try:
            await asyncio.to_thread(_run, settings)
        except Exception:
            logger.exception("Reminder worker failed; retrying in one hour.")
        await asyncio.sleep(3600)
