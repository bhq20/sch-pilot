#!/usr/bin/env bash
#
# Deploy do backend SCH no Google Cloud Run.
# Uso: ./scripts/deploy_cloudrun.sh <GCP_PROJECT_ID>
#
# Pré-requisitos:
#   - gcloud CLI instalado e autenticado (gcloud auth login)
#   - gcloud config set project <PROJECT_ID>
#   - APIs ativadas: run.googleapis.com, cloudbuild.googleapis.com,
#     artifactregistry.googleapis.com
#   - Secret Manager com DATABASE_URL e SECRET_KEY criados
#
set -euo pipefail

PROJECT_ID="${1:-}"
if [ -z "$PROJECT_ID" ]; then
  echo "uso: $0 <GCP_PROJECT_ID>"
  exit 1
fi

SERVICE=sch-backend
REGION=southamerica-east1  # São Paulo
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}:$(date +%Y%m%d-%H%M%S)"

cd "$(dirname "$0")/../backend"

echo ">> Build da imagem com Cloud Build..."
gcloud builds submit --tag "${IMAGE}" --project "${PROJECT_ID}"

echo ">> Deploy no Cloud Run..."
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 60 \
  --concurrency 40 \
  --set-env-vars "ACCESS_TOKEN_EXPIRE_MINUTES=480,ALGORITHM=HS256,CORS_ORIGINS=https://app.bhqconsultoria.com" \
  --set-secrets "DATABASE_URL=sch-database-url:latest,SECRET_KEY=sch-secret-key:latest" \
  --project "${PROJECT_ID}"

echo
echo ">> Pronto. URL pública:"
gcloud run services describe "${SERVICE}" --region "${REGION}" --project "${PROJECT_ID}" \
  --format 'value(status.url)'
