from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.db import get_session  # noqa: E402
from app.staff.models import OFFICER, ROLES  # noqa: E402
from app.staff.service import create_user, list_users, set_active, set_password  # noqa: E402

DESCRIPTION = """Manage staff accounts (US19). There is no sign-up page: accounts exist only through this script.

    python scripts/create_staff_user.py add officer@sdu.edu.kz --name "Aigerim" --role officer
    python scripts/create_staff_user.py reset-password officer@sdu.edu.kz
    python scripts/create_staff_user.py deactivate officer@sdu.edu.kz
    python scripts/create_staff_user.py list

The password is asked interactively (or read from stdin with --password-stdin) and is
never passed as an argument, so it does not end up in the shell history."""


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\n")
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        raise ValueError("passwords do not match")
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="create an account")
    add.add_argument("email")
    add.add_argument("--name", required=True)
    add.add_argument("--role", choices=ROLES, default=OFFICER)
    add.add_argument("--password-stdin", action="store_true")
    reset = commands.add_parser("reset-password", help="set a new password and log out every session")
    reset.add_argument("email")
    reset.add_argument("--password-stdin", action="store_true")
    for name, help_text in (("deactivate", "block the account and log it out"), ("activate", "unblock the account")):
        commands.add_parser(name, help=help_text).add_argument("email")
    commands.add_parser("list", help="list accounts")
    args = parser.parse_args(argv)

    with get_session(get_settings()) as session:
        try:
            if args.command == "add":
                user = create_user(session, args.email, args.name, args.role, _read_password(args.password_stdin))
                print(f"Created {user.role} {user.email}")
            elif args.command == "reset-password":
                user = set_password(session, args.email, _read_password(args.password_stdin))
                print(f"New password set for {user.email}; existing sessions are logged out")
            elif args.command in ("deactivate", "activate"):
                user = set_active(session, args.email, args.command == "activate")
                print(f"{user.email} is now {'active' if user.active else 'deactivated'}")
            else:
                for user in list_users(session):
                    last = user.last_login_at.isoformat(timespec="minutes") if user.last_login_at else "never"
                    print(f"{user.email}\t{user.role}\t{'active' if user.active else 'deactivated'}\tlast login {last}")
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
