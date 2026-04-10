#!/usr/bin/env bash
#
# SCH Pilot — Setup one-click (Linux/macOS).
# Requisitos: Docker + Docker Compose instalados.
#
set -euo pipefail

cd "$(dirname "$0")"

echo ">> Subindo stack (db + backend + frontend)..."
docker compose up -d --build

echo ">> Aguardando backend ficar pronto..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "   backend OK"
    break
  fi
  sleep 2
done

echo
echo "============================================================"
echo "  SCH Pilot pronto!"
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:8000/docs"
echo "  Login    : admin@demo.com / demo1234"
echo "============================================================"
