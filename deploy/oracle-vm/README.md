# Oracle VM deployment

Live site: https://193-123-95-102.sslip.io

The portal runs on an Oracle Cloud Always Free VM (`VM.Standard.E2.1.Micro`: x86, 1 GB RAM
plus a 2 GB swap file, Ubuntu 22.04) in `/opt/sdu-admissions`:

| Service | What |
| ------- | ---- |
| `db` | PostgreSQL 16 + pgvector, tuned for 1 GB RAM, data in the `pgdata` volume |
| `api` | backend image (slim search model, about 410 MB) |
| `web` | frontend image, nginx proxies `/api/` to `api` |
| `caddy` | ports 80/443, free HTTPS certificate from Let's Encrypt for the sslip.io name |

Volumes: `pgdata` (database) and `uploads` (Sprint 7 application documents, ADR 0003).
Both are backed up daily (see Backups). Online applications are switched off on the VM
(`APPLICATIONS_ENABLED=false` by default) until the hosting record and PO acceptance allow it.

## Automatic deployment

`.github/workflows/deploy.yml` runs on every push to `main` that changes `backend/`,
`frontend/`, `deploy/oracle-vm/` or a workflow, and on demand (Actions → Deploy → Run workflow):

1. Backend CI and Frontend CI run while GitHub builds `sdu-admissions-api:<short sha>` and
   `sdu-admissions-web:<short sha>` (the VM is too small to build the slim search model)
   and pushes them to GHCR (`ghcr.io/abdyken/...`, public packages). The build reuses
   layers through the `buildcache` tag in the same packages.
2. Only when both CI workflows and both images succeeded: `compose.yml` and `Caddyfile` go
   over SSH to `deploy.sh` on the VM. It pulls the two images (only the changed layers),
   switches to the new version and waits until every service is healthy. If the new
   version does not become healthy, it starts the previous version again and the
   workflow fails.
3. The workflow checks `/api/health` and the home page on the live site.

Run on another branch (Actions → Deploy → Run workflow, choose the branch), the workflow
runs CI and pushes images but never deploys. If GHCR is unavailable, `deploy.sh` also
accepts the old bundle: add `images.tar.gz` (`docker save` of both images) to the tar.

The API container applies new Alembic migrations when it starts. An automatic rollback
does not undo them, so keep migrations backward compatible with the previous version.

### Secrets and settings (repository → Settings)

| Name | Kind | Value |
| ---- | ---- | ----- |
| `DEPLOY_HOST` | variable | `ubuntu@193.123.95.102` |
| `DEPLOY_SSH_KEY` | secret | private half of the deploy key |
| `DEPLOY_KNOWN_HOSTS` | secret | `ssh-keyscan -t ed25519 193.123.95.102` output |

The packages `sdu-admissions-api` and `sdu-admissions-web` (GitHub profile → Packages) must
be public, so the VM pulls them without a token. They contain no secrets: those stay in `.env`.

The public half of the deploy key is in the VM's `~/.ssh/authorized_keys` with
`restrict,command="/opt/sdu-admissions/deploy.sh"`: it can only run a deployment, not a shell.

Application secrets (`POSTGRES_PASSWORD`, `GEMINI_API_KEY`) live only in
`/opt/sdu-admissions/.env` on the VM (mode 660, group `sduadmin`) and never go through GitHub. After editing
`.env`: `cd /opt/sdu-admissions && docker compose up -d`.

## By hand (on the VM)

    cd /opt/sdu-admissions
    docker compose ps
    docker compose logs -f api
    # roll back to the previous version (deploy.sh keeps its images):
    docker images sdu-admissions-api
    sed -i 's/^APP_TAG=.*/APP_TAG=<previous tag>/' .env && docker compose up -d --wait

`deploy.sh` is not deployed by the workflow (the deploy key can only run it). After changing
it, copy it to the VM: `scp deploy/oracle-vm/deploy.sh oracle-vm:/opt/sdu-admissions/`.

## Backups

`backup.sh` runs every day at 21:00 UTC (02:00 in Almaty) through the systemd timer
`sdu-admissions-backup.timer`; a run missed while the VM was off happens at the next boot.
Each run writes `/var/backups/sdu-admissions/<UTC time>/` (mode 700, user `ubuntu`, it holds
personal data):

| File | What |
| ---- | ---- |
| `database.dump` | `pg_dump --format=custom`, checked with `pg_restore --list` |
| `database.list` | the dump's table of contents |
| `uploads.tar.gz` | the `uploads` volume, checked with `gzip -t` |
| `SHA256SUMS` | checksums of both |

Backups older than 14 days are deleted, but the newest three are always kept. The script
refuses to run with less than 3 GB free. Check it with:

    systemctl list-timers sdu-admissions-backup.timer
    journalctl -u sdu-admissions-backup.service -n 20
    sudo systemctl start sdu-admissions-backup.service   # a backup now

The backups are on the same disk as the data: they protect against mistakes, a bad
migration and deleted files, not against losing the VM. Copy one off the server from time
to time, e.g. `scp -r oracle-vm:/var/backups/sdu-admissions/<time> .` to an encrypted disk.

**Restore** (stop the API first so nothing writes during the restore):

    cd /opt/sdu-admissions && B=/var/backups/sdu-admissions/<time>
    (cd $B && sha256sum -c SHA256SUMS)
    docker compose stop api
    docker compose exec -T db sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
    docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < $B/database.dump
    docker run --rm -v sdu-admissions_uploads:/var/lib/sdu-admissions/uploads -v $B:/backup:ro alpine \
      sh -c 'rm -rf /var/lib/sdu-admissions/uploads/* && tar -xzf /backup/uploads.tar.gz -C /var/lib/sdu-admissions'
    docker compose up -d --wait

To test a backup without touching production, restore the dump into a scratch database
(`createdb restore_check`, `pg_restore -d restore_check ...`, compare counts, `dropdb
restore_check`); this was done on 20.11.2026 and matched the live database.

Installing (already done on the current VM; repeat on a new one):

    scp deploy/oracle-vm/backup.sh oracle-vm:/opt/sdu-admissions/
    scp deploy/oracle-vm/systemd/sdu-admissions-backup.* oracle-vm:/tmp/
    sudo install -d -m 700 -o ubuntu -g ubuntu /var/backups/sdu-admissions
    sudo install -m 644 /tmp/sdu-admissions-backup.service /tmp/sdu-admissions-backup.timer /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now sdu-admissions-backup.timer

Like `deploy.sh`, `backup.sh` is not deployed by the workflow: copy it after changing it.

## Setting up a new VM

1. Install Docker Engine with the compose plugin and add `ubuntu` to the `docker` group; add swap.
2. Copy `compose.yml`, `Caddyfile` and `deploy.sh` to `/opt/sdu-admissions` and create
   `.env` (mode 600) with `APP_TAG`, `SITE_HOST`, `POSTGRES_PASSWORD` and `GEMINI_API_KEY`.
3. Open TCP 80 and 443 in the subnet's security list.
4. Add the deploy key to `authorized_keys` as above, update the secrets, and run the
   Deploy workflow.
5. Install the daily backup (see Backups).
