# README

## Deploying the Docker Container
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

docker tag hotel-cancellation-serving \
  us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v1

docker push \
  us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v1

docker buildx build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v3 \
  -f serving/Dockerfile \
  --push \
  .
```

## Registering the model
```bash
gcloud ai models upload \
  --region=us-central1 \
  --display-name=hotel-cancellation-model-v3 \
  --artifact-uri=gs://burner-neisincl-ml-pipeline-artefacts/models/hotel-cancellation/ \
  --container-image-uri=us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v3 \
  --container-health-route=/health \
  --container-predict-route=/predict \
  --container-ports=8080
```