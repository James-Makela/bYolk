#!/bin/sh

npm install
npm run build:css

set -a
. ./.env
set +a

echo "CONTAINER_RUNTIME is: $CONTAINER_RUNTIME"

CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-docker}"

case "$CONTAINER_RUNTIME" in
  docker|podman)
    echo "Using: $CONTAINER_RUNTIME"
    ;;
  *)
    echo "Error: Unknown runtime '$CONTAINER_RUNTIME'. Use 'docker' or 'podman'." >&2
    exit 1
    ;;
esac

if [ "$CONTAINER_RUNTIME" = "docker" ]; then
  COMPOSE_CMD="sudo docker compose"
else
  COMPOSE_CMD="podman compose"
fi

$COMPOSE_CMD up -d
