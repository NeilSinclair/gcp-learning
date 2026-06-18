# Hotel Cancellation MLOps Pipeline

## Architecture

```text
GitHub
  ↓
Cloud Build Trigger
  ↓
Build Training Image
  ↓
Push Training Image → Artifact Registry

Build Serving Image
  ↓
Push Serving Image → Artifact Registry

Run Vertex Pipeline
  ↓
Custom Training Job
  ↓
Save model.joblib to GCS
  ↓
Import Model
  ↓
Upload Model to Vertex Model Registry
  ↓
Deploy Model to Vertex Endpoint
```

---

## Key Components

### Training Image

Purpose:
- Loads data from BigQuery
- Trains model
- Saves model artifact to GCS

Location:

```text
training/
├── Dockerfile
├── train.py
└── requirements.txt
```

Artifact location:

```text
gs://burner-neisincl-ml-pipeline-artefacts/models/hotel-cancellation-vertex-training/
```

---

### Serving Image

Purpose:
- Loads model.joblib
- Exposes /predict endpoint
- Exposes /health endpoint

Location:

```text
serving/
├── Dockerfile
├── app.py
└── requirements.txt
```

---

### Vertex Pipeline

Location:

```text
pipelines/
├── hotel_pipeline.py
├── compile_pipeline.py
└── run_pipeline.py
```

Pipeline steps:

1. Run CustomTrainingJobOp using training image
2. Import serving container
3. Upload model to Vertex Model Registry
4. Deploy model to endpoint

---

## Cloud Build

Location:

```text
cloudbuild.yaml
```

Responsibilities:

1. Build training image
2. Push training image
3. Build serving image
4. Push serving image
5. Compile pipeline
6. Run pipeline

The pipeline receives:

```python
training_image_uri
serving_image_uri
```

as parameters.

---

## Important GCP Resources

### Artifact Registry

Repository:

```text
ml-models
```

Contains:

```text
hotel-training
hotel-cancellation
```

---

### GCS Bucket

```text
gs://burner-neisincl-ml-pipeline-artefacts
```

Equivalent to:
- AWS S3
- Azure Blob Storage

Used for:
- Model artifacts
- Pipeline outputs
- Pipeline metadata

---

### Endpoint

Endpoint IDs are stable.

Models are deployed to endpoints.

Cost comes from deployed replicas, NOT from the endpoint itself.

Safe:

```text
Endpoint exists
No deployed model
```

Costs money:

```text
Endpoint exists
Model deployed
```

---

## Common Gotchas

### ARM Images

Vertex Prediction requires x86 containers.

Build images in Cloud Build rather than locally on Apple Silicon.

---

### AIP_STORAGE_URI

Do not attempt:

```python
joblib.load("gs://...")
```

Download the file locally first.

---

### Metadata Store Permission

If pipeline creation fails with:

```text
aiplatform.metadataStores.get
```

Grant:

```text
roles/aiplatform.user
```

to the compute service account.

---

### Bucket Permissions

Pipeline execution requires bucket permissions on:

```text
gs://burner-neisincl-ml-pipeline-artefacts
```

Common required roles:

```text
storage.objectAdmin
storage.admin
```

---

### Cloud Build Permissions

Common required roles:

```text
roles/aiplatform.admin
roles/artifactregistry.writer
roles/logging.logWriter
roles/bigquery.jobUser
roles/bigquery.dataViewer
```

---

## Useful Commands

List endpoints:

```bash
gcloud ai endpoints list --region=us-central1
```

Create endpoint:

```bash
gcloud ai endpoints create \
  --region=us-central1 \
  --display-name=hotel-cancellation-endpoint
```

Deploy model manually:

```bash
gcloud ai endpoints deploy-model ...
```

Run pipeline locally:

```bash
python compile_pipeline.py

python run_pipeline.py \
  --training-image-uri <training-image> \
  --serving-image-uri <serving-image>
```

---

## Next Improvements

- Add deployment gate (only deploy if metrics improve)
- Schedule retraining
- Add model monitoring
- Add drift detection
- Add endpoint auto-creation/reuse
- Add rollback strategy
- Separate dev and prod endpoints
```
:::
