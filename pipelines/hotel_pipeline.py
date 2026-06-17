from kfp import dsl
from kfp.dsl import importer
from google_cloud_pipeline_components.types import artifact_types
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp
from google_cloud_pipeline_components.v1.model import ModelUploadOp
from google_cloud_pipeline_components.v1.endpoint import ModelDeployOp
from google_cloud_pipeline_components.types import artifact_types


PROJECT_ID = "burner-neisincl"
REGION = "us-central1"

TRAINING_IMAGE = "us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-training:v1"
SERVING_IMAGE = "us-central1-docker.pkg.dev/burner-neisincl/ml-models/hotel-cancellation:v3"

MODEL_ARTIFACT_URI = "gs://burner-neisincl-ml-pipeline-artefacts/models/hotel-cancellation-vertex-training/"
ENDPOINT_ID = "5254179590804340736"


@dsl.pipeline(name="hotel-cancellation-pipeline")
def hotel_pipeline():
    train_job = CustomTrainingJobOp(
        display_name="hotel-training",
        project=PROJECT_ID,
        location=REGION,
        worker_pool_specs=[
            {
                "machine_spec": {"machine_type": "e2-standard-4"},
                "replica_count": 1,
                "container_spec": {"image_uri": TRAINING_IMAGE},
            }
        ],
    )

    imported_model = importer(
        artifact_uri=MODEL_ARTIFACT_URI,
        artifact_class=artifact_types.UnmanagedContainerModel,
        metadata={
            "containerSpec": {
                "imageUri": SERVING_IMAGE,
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

    deploy_model = ModelDeployOp(
        model=upload_model.outputs["model"],
        endpoint=existing_endpoint.outputs["artifact"],
        deployed_model_display_name="hotel-cancellation-pipeline-deployment",
        traffic_split={"0": 100},
        dedicated_resources_machine_type="e2-standard-2",
        dedicated_resources_min_replica_count=1,
        dedicated_resources_max_replica_count=1,
    )