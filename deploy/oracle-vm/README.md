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

## Automatic deployment

`.github/workflows/deploy.yml` runs on every push to `main` that changes `backend/`,
`frontend/`, `deploy/oracle-vm/` or a workflow, and on demand (Actions → Deploy → Run workflow):

1. Backend CI and Frontend CI run first; a failure stops the deployment.
2. GitHub builds `sdu-admissions-api:<short sha>` and `sdu-admissions-web:<short sha>`
   (the VM is too small to build the slim search model).
3. The images, `compose.yml` and `Caddyfile` go over SSH to `deploy.sh` on the VM. It
   switches to the new version and waits until every service is healthy. If the new
   version does not become healthy, it starts the previous version again and the
   workflow fails.
4. The workflow checks `/api/health` and the home page on the live site.

The API container applies new Alembic migrations when it starts. An automatic rollback
does not undo them, so keep migrations backward compatible with the previous version.

### Secrets and settings (repository → Settings)

| Name | Kind | Value |
| ---- | ---- | ----- |
| `DEPLOY_HOST` | variable | `ubuntu@193.123.95.102` |
| `DEPLOY_SSH_KEY` | secret | private half of the deploy key |
| `DEPLOY_KNOWN_HOSTS` | secret | `ssh-keyscan -t ed25519 193.123.95.102` output |

The public half of the deploy key is in the VM's `~/.ssh/authorized_keys` with
`restrict,command="/opt/sdu-admissions/deploy.sh"`: it can only run a deployment, not a shell.

Application secrets (`POSTGRES_PASSWORD`, `GEMINI_API_KEY`) live only in
`/opt/sdu-admissions/.env` on the VM (mode 600) and never go through GitHub. After editing
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

## Setting up a new VM

1. Install Docker Engine with the compose plugin and add `ubuntu` to the `docker` group; add swap.
2. Copy `compose.yml`, `Caddyfile` and `deploy.sh` to `/opt/sdu-admissions` and create
   `.env` (mode 600) with `APP_TAG`, `SITE_HOST`, `POSTGRES_PASSWORD` and `GEMINI_API_KEY`.
3. Open TCP 80 and 443 in the subnet's security list.
4. Add the deploy key to `authorized_keys` as above, update the secrets, and run the
   Deploy workflow.
