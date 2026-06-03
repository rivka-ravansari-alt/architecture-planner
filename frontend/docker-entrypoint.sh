#!/bin/sh
set -eu

export PORT="${PORT:-8080}"
export BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8080}"

if [ -z "${BACKEND_URL}" ]; then
  echo "BACKEND_URL is required (e.g. https://archsari-api-xxxxx.run.app)" >&2
  exit 1
fi

envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
