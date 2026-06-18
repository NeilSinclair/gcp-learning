from kfp import dsl
from kfp.dsl import importer, component
from google_cloud_pipeline_components.types import artifact_types
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp
from google_cloud_pipeline_components.v1.model import ModelUploadOp
from google_cloud_pipeline_components.v1.endpoint import ModelDeployOp
from google_cloud_pipeline_components.types import artifact_types


PROJECT_ID = "burner-neisincl"
REGION = "us-central1"

ENDPOINT_ID = "1341395939549511680"

MODEL_BUCKET = "burner-neisincl-ml-pipeline-artefacts"
MODEL_PREFIX = "models/hotel-cancellation-vertex-training"

MODEL_ARTIFACT_URI = f"gs://{MODEL_BUCKET}/{MODEL_PREFIX}"

CANDIDATE_METRICS_URI = (
    f"{MODEL_ARTIFACT_URI}/candidates/metrics.json"
)

PRODUCTION_METRICS_URI = (
    f"{MODEL_ARTIFACT_URI}/production/metrics.json"
)

@component(
    base_image="python:3.12",
    packages_to_install=["google-cloud-storage"],
)
def deployment_gate(
    candidate_metrics_uri: str,
    production_metrics_uri: str,
) -> str:

    import json
    from google.cloud import storage

    storage_client = storage.Client()

    def load_metrics(uri: str):
        bucket_name = uri.replace("gs://", "").split("/")[0]
        blob_path = "/".join(uri.replace("gs://", "").split("/")[1:])

        bucket = storage_client.bucket(bucket_name)

        return json.loads(bucket.blob(blob_path).download_as_text())

    candidate = load_metrics(candidate_metrics_uri)

    candidate_auc = float(candidate["auc"])

    print(f"Candidate AUC = {candidate_auc}")

    try:
        production = load_metrics(production_metrics_uri)
        production_auc = float(production["auc"])

    except Exception:
        print("No production metrics found")
        return "DEPLOY"

    print(f"Production AUC = {production_auc}")

    if candidate_auc > production_auc:
        return "DEPLOY"

    return "SKIP"


@component(
    base_image="python:3.12",
    packages_to_install=["google-cloud-storage"],
)
def promote_metrics(
    candidate_metrics_uri: str,
    production_metrics_uri: str,
):

    from google.cloud import storage

    storage_client = storage.Client()

    def parse_uri(uri):

        bucket_name = uri.replace(
            "gs://",
            ""
        ).split("/")[0]

        blob_path = "/".join(
            uri.replace(
                "gs://",
                ""
            ).split("/")[1:]
        )

        return bucket_name, blob_path

    candidate_bucket, candidate_blob = (
        parse_uri(candidate_metrics_uri)
    )

    production_bucket, production_blob = (
        parse_uri(production_metrics_uri)
    )

    source_bucket = storage_client.bucket(
        candidate_bucket
    )

    destination_bucket = (
        storage_client.bucket(
            production_bucket
        )
    )

    source_bucket.copy_blob(
        source_bucket.blob(candidate_blob),
        destination_bucket,
        production_blob,
    )


@dsl.pipeline(name="hotel-cancellation-pipeline")
def hotel_pipeline(
    training_image_uri: str,
    serving_image_uri: str,
):
    train_job = CustomTrainingJobOp(
        display_name="hotel-training",
        project=PROJECT_ID,
        location=REGION,
        worker_pool_specs=[
            {
                "machine_spec": {"machine_type": "e2-standard-4"},
                "replica_count": 1,
                "container_spec": {"image_uri": training_image_uri},
            }
        ],
    )

    imported_model = importer(
        artifact_uri=MODEL_ARTIFACT_URI,
        artifact_class=artifact_types.UnmanagedContainerModel,
        metadata={
            "containerSpec": {
                "imageUri": serving_image_uri,
                "predictRoute": "/predict",
                "healthRoute": "/health",
                "ports": [{"containerPort": 8080}],
            }
        },
    ).after(train_job)

    upload_model = ModelUploadOp(
        project=PROJECT_ID,
        location=REGION,
        display_name="hotel-cancellation-pipeline-model",
        unmanaged_container_model=imported_model.outputs["artifact"],
    )

    existing_endpoint = importer(
        artifact_uri=f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}",
        artifact_class=artifact_types.VertexEndpoint,
        metadata={
            "resourceName": f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}",
        },
    )

    gate = deployment_gate(candidate_metrics_uri=CANDIDATE_METRICS_URI, production_metrics_uri=PRODUCTION_METRICS_URI)
    gate.after(upload_model)

    with dsl.If(gate.output == "DEPLOY"):
        deploy_model = ModelDeployOp(
            model=upload_model.outputs["model"],
            endpoint=existing_endpoint.outputs["artifact"],
            deployed_model_display_name="hotel-cancellation-pipeline-deployment",
            traffic_split={"0": 100},
            dedicated_resources_machine_type="e2-standard-2",
            dedicated_resources_min_replica_count=1,
            dedicated_resources_max_replica_count=1,
        )

        promote = promote_metrics(
            candidate_metrics_uri=CANDIDATE_METRICS_URI,
            production_metrics_uri=PRODUCTION_METRICS_URI
        )


        promote.after(deploy_model)