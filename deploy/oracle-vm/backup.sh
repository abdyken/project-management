#!/usr/bin/env bash
# Daily backup of the database and the uploaded documents (Sprint 7 CO.7, ADR 0003).
# Run by sdu-admissions-backup.timer; by hand: /opt/sdu-admissions/backup.sh
set -euo pipefail
umask 077

APP_DIR=${APP_DIR:-/opt/sdu-admissions}
BACKUP_DIR=${BACKUP_DIR:-/var/backups/sdu-admissions}
KEEP_DAYS=${KEEP_DAYS:-14}
# Leave room for the database and new uploads (the API pauses uploads below 2 GB).
MIN_FREE_KB=${MIN_FREE_KB:-3145728}

cd "$APP_DIR"
mkdir -p "$BACKUP_DIR"
free_kb=$(df -Pk "$BACKUP_DIR" | awk 'NR == 2 {print $4}')
if [ "$free_kb" -lt "$MIN_FREE_KB" ]; then
  echo "backup: only $((free_kb / 1024)) MB free, need $((MIN_FREE_KB / 1024)) MB" >&2
  exit 1
fi

stamp=$(date -u +%Y%m%dT%H%M%SZ)
work="$BACKUP_DIR/.partial-$stamp"
mkdir "$work"
trap 'rm -rf "$work"' EXIT

# Database: custom-format dump, checked by listing its contents.
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$work/database.dump"
docker compose exec -T db pg_restore --list < "$work/database.dump" > "$work/database.list"
[ -s "$work/database.list" ]

# Uploads: read through the API container, which mounts the volume; compressed here.
docker compose exec -T api tar -C /var/lib/sdu-admissions -cf - uploads | gzip -6 > "$work/uploads.tar.gz"
gzip -t "$work/uploads.tar.gz"
tar -tzf "$work/uploads.tar.gz" > /dev/null

(cd "$work" && sha256sum database.dump uploads.tar.gz > SHA256SUMS)
mv "$work" "$BACKUP_DIR/$stamp"
trap - EXIT

# Keep KEEP_DAYS days, but never delete the newest three backups.
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -name '20*Z' | sort -r | tail -n +4 |
  while read -r old; do
    if [ -n "$(find "$old" -maxdepth 0 -mtime +"$KEEP_DAYS")" ]; then rm -rf "$old"; fi
  done

files=$(tar -tzf "$BACKUP_DIR/$stamp/uploads.tar.gz" | grep -vc '/$' || true)
echo "backup: $stamp ok, database $(du -h "$BACKUP_DIR/$stamp/database.dump" | cut -f1), uploads $files file(s), $(du -sh "$BACKUP_DIR/$stamp" | cut -f1) in total"
