#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="burner-neisincl"
SA="985136436720-compute@developer.gserviceaccount.com"
BUCKET="burner-neisincl-ml-pipeline-artefacts"

echo "Granting project-level roles to $SA..."

for ROLE in \
  roles/aiplatform.admin \
  roles/artifactregistry.writer \
  roles/logging.logWriter \
  roles/bigquery.jobUser \
  roles/bigquery.dataViewer
do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA" \
    --role="$ROLE"
done

echo "Granting bucket-level Storage Object Admin..."

gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:$SA" \
  --role="roles/storage.objectAdmin"

echo "Done."