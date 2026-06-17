# Vertex Pipelines Notes

## Common IAM Issues

### Metadata Store Permission

Error:

```text
aiplatform.metadataStores.get denied
```

Fix:

```bash
gcloud projects add-iam-policy-binding burner-neisincl \
  --member="serviceAccount:985136436720-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.admin"
```

---

### Pipeline Root Bucket Permission

Error:

```text
storage.objects.get
storage.objects.create
```

Fix:

```bash
gcloud storage buckets add-iam-policy-binding \
  gs://burner-neisincl-ml-pipeline-artefacts \
  --member="serviceAccount:985136436720-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

---

## Required Pipeline Configuration

```python
job = aiplatform.PipelineJob(
    display_name="hotel-cancellation-pipeline",
    template_path="hotel_pipeline.json",
    pipeline_root="gs://burner-neisincl-ml-pipeline-artefacts/pipeline-root/",
)

job.run(
    service_account="985136436720-compute@developer.gserviceaccount.com"
)
```

---

## Useful Concepts

- `gs://...` = GCP Cloud Storage bucket (similar to S3).
- `pipeline_root` = location where Vertex stores pipeline artifacts and metadata.
- Pipeline runtime identity = service account passed to `job.run(...)`.
- Most IAM problems can be broken down into:
  1. Which identity is making the request?
  2. Which resource is being accessed?
  3. Which permission is missing?

---

## Working Architecture

```text
BigQuery
  ↓
Vertex Pipeline
  ↓
Vertex Custom Training Job
  ↓
model.joblib
  ↓
Cloud Storage
  ↓
Model Registry
  ↓
Endpoint
```