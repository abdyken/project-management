from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.conversation.service import delete_expired_turns
from app.db import get_session

logger = logging.getLogger(__name__)

PURGE_INTERVAL_SECONDS = 24 * 60 * 60


def purge_once(settings: Settings) -> int | None:
    try:
        with get_session(settings) as session:
            deleted = delete_expired_turns(session)
    except Exception as error:
        logger.warning("chat turn purge failed: %s", type(error).__name__)
        return None
    logger.info("chat turn purge deleted=%d", deleted)
    return deleted


async def purge_daily(settings: Settings, interval_seconds: float = PURGE_INTERVAL_SECONDS) -> None:
    while True:
        await asyncio.to_thread(purge_once, settings)
        await asyncio.sleep(interval_seconds)
