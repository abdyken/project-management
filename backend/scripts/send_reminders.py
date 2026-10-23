"""Run the same idempotent reminder job as the API's hourly worker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.applicant.reminders import send_due_reminders
from app.config import get_settings
from app.db import get_session

if __name__ == "__main__":
    settings = get_settings()
    with get_session(settings) as session:
        print(f"Sent {send_due_reminders(session, settings)} reminder(s).")
