"""Status rules, US6 status texts and status e-mails for applications (ADR 0002, 0004)."""

from __future__ import annotations

import logging
import smtplib
from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.applicant import mail
from app.applicant.models import Applicant
from app.applicant.service import now
from app.applications.models import (
    ACCEPTED,
    DRAFT,
    IN_REVIEW,
    NEEDS_CHANGES,
    REJECTED,
    SUBMITTED,
    Application,
)
from app.catalogue.models import Program
from app.config import Settings

logger = logging.getLogger(__name__)

# Staff may move an application from the key to any of the listed statuses.
STAFF_TRANSITIONS = {
    SUBMITTED: (IN_REVIEW, NEEDS_CHANGES, ACCEPTED, REJECTED),
    IN_REVIEW: (NEEDS_CHANGES, ACCEPTED, REJECTED),
}
NOTE_REQUIRED = (NEEDS_CHANGES, REJECTED)
# Statuses the applicant is e-mailed about; the others they see in the account.
NOTIFY = (NEEDS_CHANGES, ACCEPTED, REJECTED)

# Stage and next step per status (US6); {title} is the programme in the applicant's language.
STATUS_TEXT = {
    "en": {
        DRAFT: ("{title}: draft, not sent yet.", "Fill in the form, attach your documents and submit it."),
        SUBMITTED: ("{title}: submitted, waiting for review.", "Nothing to do now; we e-mail you when it changes."),
        IN_REVIEW: ("{title}: being reviewed by the admissions office.", "Nothing to do now; we e-mail you when it changes."),
        NEEDS_CHANGES: ("{title}: the office asked for changes.", "Read the office's note in your account, correct the application and submit it again."),
        ACCEPTED: ("{title}: accepted, your documents are complete.", "Bring the originals to the Admissions Office before the deadline. This is not yet an admission decision."),
        REJECTED: ("{title}: not accepted.", "Read the office's note in your account. You can start a new application."),
    },
    "ru": {
        DRAFT: ("{title}: черновик, ещё не отправлен.", "Заполните форму, прикрепите документы и отправьте заявку."),
        SUBMITTED: ("{title}: отправлена, ожидает проверки.", "Сейчас ничего делать не нужно; мы напишем на почту, когда статус изменится."),
        IN_REVIEW: ("{title}: проверяется приёмной комиссией.", "Сейчас ничего делать не нужно; мы напишем на почту, когда статус изменится."),
        NEEDS_CHANGES: ("{title}: комиссия просит внести исправления.", "Прочитайте комментарий комиссии в личном кабинете, исправьте заявку и отправьте её снова."),
        ACCEPTED: ("{title}: принята, документы полные.", "Принесите оригиналы в приёмную комиссию до срока. Это ещё не решение о зачислении."),
        REJECTED: ("{title}: не принята.", "Прочитайте комментарий комиссии в личном кабинете. Вы можете подать новую заявку."),
    },
    "kk": {
        DRAFT: ("{title}: жоба, әлі жіберілмеген.", "Форманы толтырып, құжаттарды тіркеп, өтінішті жіберіңіз."),
        SUBMITTED: ("{title}: жіберілді, тексеруді күтуде.", "Қазір ештеңе істеудің қажеті жоқ; мәртебе өзгергенде поштаға жазамыз."),
        IN_REVIEW: ("{title}: қабылдау комиссиясы тексеруде.", "Қазір ештеңе істеудің қажеті жоқ; мәртебе өзгергенде поштаға жазамыз."),
        NEEDS_CHANGES: ("{title}: комиссия түзетулер енгізуді сұрайды.", "Жеке кабинеттегі комиссия пікірін оқып, өтінішті түзетіп, қайта жіберіңіз."),
        ACCEPTED: ("{title}: қабылданды, құжаттар толық.", "Түпнұсқаларды мерзімге дейін қабылдау комиссиясына әкеліңіз. Бұл әлі оқуға қабылдау туралы шешім емес."),
        REJECTED: ("{title}: қабылданбады.", "Жеке кабинеттегі комиссия пікірін оқыңыз. Жаңа өтініш бере аласыз."),
    },
}
NO_APPLICATIONS = {
    "en": "You have no applications yet. Save a programme's checklist, then start an application in your account.",
    "ru": "У вас пока нет заявок. Сохраните чек-лист программы и начните заявку в личном кабинете.",
    "kk": "Сізде әлі өтініш жоқ. Бағдарламаның чек-парағын сақтап, жеке кабинетте өтініш бастаңыз.",
}
ANONYMOUS_STATUS = {
    "en": "You can follow your applications under My applications in your account (/account/applications). If you are logged in, your current status appears right below.",
    "ru": "Следить за заявками можно в личном кабинете в разделе «Мои заявки» (/account/applications). Если вы вошли в аккаунт, текущий статус появится ниже.",
    "kk": "Өтініштеріңізді жеке кабинеттегі «Менің өтініштерім» бөлімінен қадағалай аласыз (/account/applications). Аккаунтқа кірген болсаңыз, ағымдағы мәртебе төменде шығады.",
}
EMAIL_TEXT = {
    "en": ("SDU: your application status changed", "Open your application"),
    "ru": ("SDU: статус вашей заявки изменился", "Открыть заявку"),
    "kk": ("SDU: өтініш мәртебесі өзгерді", "Өтінішті ашу"),
}


def program_title(program: Program | None, language: str) -> str:
    if program is None:
        return ""
    return getattr(program, f"title_{language}", None) or program.title


def status_lines(session: Session, applications: list[Application], language: str) -> list[tuple[str, str]]:
    texts = STATUS_TEXT[language]
    lines = []
    for application in applications:
        stage, next_step = texts[application.status]
        title = program_title(session.get(Program, application.program_id), language)
        lines.append((stage.format(title=f"{title} ({application.program_id})"), next_step))
    return lines


def status_answer(session: Session, applicant: Applicant, language: str) -> str:
    """US6: the chat answer about the applicant's own applications, built from the database."""
    applications = list(
        session.scalars(
            select(Application)
            .where(Application.applicant_id == applicant.id)
            .order_by(Application.updated_at.desc(), Application.id.desc())
        )
    )
    if not applications:
        return NO_APPLICATIONS[language]
    return "\n\n".join(f"{stage}\n{next_step}" for stage, next_step in status_lines(session, applications, language))


def _notify(session: Session, settings: Settings, application_id: int) -> bool:
    """E-mail the applicant about the current status once.

    The row is claimed (notified_status set) and the lock released before talking to SMTP,
    so a slow mail server never blocks the applicant or staff. A failed send gives the claim
    back for the hourly retry; a crash between claim and send loses that one e-mail.
    """
    application = session.scalar(
        select(Application)
        .where(
            Application.id == application_id,
            Application.status.in_(NOTIFY),
            or_(Application.notified_status.is_(None), Application.notified_status != Application.status),
        )
        .with_for_update(skip_locked=True)
    )
    user = session.get(Applicant, application.applicant_id) if application is not None else None
    if application is None or not user or not user.verified:
        session.commit()
        return False
    status, recipient, language = application.status, user.email, application.language
    subject, link_text = EMAIL_TEXT[language]
    stage, next_step = status_lines(session, [application], language)[0]
    # The office's note stays in the account; the e-mail carries no personal details.
    body = (
        f"{stage}\n{next_step}\n\n{link_text}: "
        f"{settings.public_base_url.rstrip('/')}/account/applications/{application.id}\n"
    )
    application.notified_status = status
    session.commit()
    try:
        mail.send_mail(settings, recipient, subject, body)
    except (OSError, smtplib.SMTPException):
        session.rollback()
        session.execute(
            update(Application)
            .where(Application.id == application_id, Application.status == status, Application.notified_status == status)
            .values(notified_status=None)
        )
        session.commit()
        raise
    return True


def notify_now(open_session: Callable[[], AbstractContextManager[Session]], settings: Settings, application_id: int) -> None:
    """Background task after a staff status change; the hourly run retries failures."""
    if not (settings.applicant_accounts_enabled and settings.applications_enabled and settings.smtp_host):
        return
    try:
        with open_session() as session:
            _notify(session, settings, application_id)
    except (OSError, smtplib.SMTPException) as error:
        logger.warning("Application status e-mail failed (%s); the hourly run retries it.", mail.describe_error(error))
    except Exception:
        logger.exception("Application status e-mail failed; the hourly run retries it.")


def send_status_notifications(session: Session, settings: Settings) -> int:
    """Hourly retry for status e-mails that failed."""
    if not (settings.applicant_accounts_enabled and settings.applications_enabled and settings.smtp_host):
        return 0
    ids = list(
        session.scalars(
            select(Application.id).where(
                Application.status.in_(NOTIFY),
                or_(Application.notified_status.is_(None), Application.notified_status != Application.status),
            )
        )
    )
    sent = 0
    for application_id in ids:
        try:
            sent += _notify(session, settings, application_id)
        except (OSError, smtplib.SMTPException) as error:
            logger.warning("Application status e-mail failed (%s); retried next run.", mail.describe_error(error))
            if mail.stops_batch(error):
                break
    return sent


def touch(application: Application) -> None:
    application.updated_at = now()


def storage_maintenance(session: Session, settings: Settings) -> None:
    """Hourly: delete drafts nobody touched for `draft_retention_days`, then orphaned files."""
    from datetime import timedelta

    from app.applications import storage
    from app.applications.models import ApplicationDocument

    if not settings.applications_enabled:
        return
    stale = select(Application.id).where(
        Application.status == DRAFT, Application.updated_at < now() - timedelta(days=settings.draft_retention_days)
    )
    keys = list(
        session.scalars(select(ApplicationDocument.storage_key).where(ApplicationDocument.application_id.in_(stale)))
    )
    deleted = session.execute(delete(Application).where(Application.id.in_(stale))).rowcount
    session.commit()
    storage.delete_files(settings, keys)
    if deleted:
        logger.info("Deleted %d stale draft application(s).", deleted)
    known = set(session.scalars(select(ApplicationDocument.storage_key)))
    storage.sweep_orphans(settings, known)
