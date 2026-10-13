#!/bin/sh
# Deploys one version of the portal on the VM. GitHub Actions runs it through the deploy
# key in ~/.ssh/authorized_keys, which may run nothing else (see README.md):
#   restrict,command="/opt/sdu-admissions/deploy.sh" ssh-ed25519 ... github-actions-deploy
# SSH_ORIGINAL_COMMAND is "deploy <git sha>"; stdin is a tar with compose.yml, Caddyfile and
# images.tar.gz (docker save of sdu-admissions-api:<sha> and sdu-admissions-web:<sha>).
# If the new version does not become healthy, the previous one is started again.
set -eu
set -f

APP_DIR=${APP_DIR:-/opt/sdu-admissions}
cd "$APP_DIR"

# Split on purpose ("deploy <sha>"); globbing is off.
# shellcheck disable=SC2086
set -- ${SSH_ORIGINAL_COMMAND:-}
if [ "$#" -ne 2 ] || [ "$1" != deploy ] || ! printf '%s' "$2" | grep -Eqx '[0-9a-f]{7,40}'; then
    echo "usage: deploy <git sha>" >&2
    exit 2
fi
tag=$2

exec 9>"$APP_DIR/.deploy.lock"
flock -n 9 || { echo "another deploy is running" >&2; exit 1; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
tar -x -C "$work" -f - compose.yml Caddyfile images.tar.gz
gunzip -c "$work/images.tar.gz" | docker load
for image in sdu-admissions-api sdu-admissions-web; do
    docker image inspect "$image:$tag" >/dev/null
done

previous=$(sed -n 's/^APP_TAG=//p' .env)
cp compose.yml compose.yml.previous
cp Caddyfile Caddyfile.previous

# tag, compose file, Caddyfile. The Caddyfile is rewritten in place because Caddy
# bind-mounts that exact file.
switch_to() {
    cp "$2" compose.yml &&
        cat "$3" >Caddyfile &&
        sed -i "s/^APP_TAG=.*/APP_TAG=$1/" .env &&
        docker compose up -d --remove-orphans --wait --wait-timeout 300 &&
        docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
}

echo "deploying $tag (running: $previous)"
if switch_to "$tag" "$work/compose.yml" "$work/Caddyfile"; then
    # Keep the new and the previous version for a manual rollback; remove older ones.
    for image in sdu-admissions-api sdu-admissions-web; do
        docker images --format '{{.Repository}}:{{.Tag}}' "$image" |
            grep -vxF -e "$image:$tag" -e "$image:$previous" | xargs -r docker rmi >/dev/null || true
    done
    docker image prune -f >/dev/null || true
    echo "deployed $tag"
else
    echo "$tag did not become healthy, starting $previous again" >&2
    docker compose logs --tail 60 api >&2 || true
    switch_to "$previous" compose.yml.previous Caddyfile.previous
    exit 1
fi
