"""Manually retry pending US30 notifications (also run by the hourly API worker)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.applicant.requests import send_request_notifications
from app.config import get_settings
from app.db import get_session

if __name__ == "__main__":
    settings = get_settings()
    with get_session(settings) as session:
        print(f"Sent {send_request_notifications(session, settings)} notification(s).")
