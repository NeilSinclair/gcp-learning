# README

## Push Dockerfile

```bash
docker buildx build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-training:v1 \
  -f training/Dockerfile \
  --push \
  .
```

## Launch custom training

- I use an e2-standard-4 here even though it's technically not allowed in the burner docs.

```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=hotel-cancellation-training-job \
  --worker-pool-spec=machine-type=e2-standard-4,replica-count=1,container-image-uri=us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-training:v1 \
  --args=""
```

## Register the model

```bash
gcloud ai models upload \
  --region=us-central1 \
  --display-name=hotel-cancellation-vertex-trained \
  --artifact-uri=gs://burner-neisincl-ml-pipeline-artefacts/models/hotel-cancellation-vertex-training/ \
  --container-image-uri=us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v3 \
  --container-health-route=/health \
  --container-predict-route=/predict \
  --container-ports=8080
```

## Deploying the endpoint

1. Get the model id

```bash
gcloud ai models list \
  --region=us-central1
```

2. Create the endpoint

```bash
gcloud ai endpoints create \
  --region=us-central1 \
  --display-name=hotel-cancellation-endpoint-v2
```

3. Get the endpoint ID:
```bash
gcloud ai endpoints list \
  --region=us-central1
```

4. Deploy the Endpoint
```bash
gcloud ai endpoints deploy-model <ENDPOINT_ID> \
  --region=us-central1 \
  --model=<MODEL_ID> \
  --display-name=hotel-cancellation-deployment \
  --machine-type=e2-standard-2 \
  --traffic-split=0=100
```

gcloud ai endpoints deploy-model 5254179590804340736 \
  --region=us-central1 \
  --model=6928683023349055488 \
  --display-name=hotel-cancellation-deployment \
  --machine-type=e2-standard-2 \
  --traffic-split=0=100