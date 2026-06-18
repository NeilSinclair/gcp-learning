import argparse

from google.cloud import aiplatform


PROJECT_ID = "burner-neisincl"
REGION = "us-central1"
PIPELINE_ROOT = "gs://burner-neisincl-ml-pipeline-artefacts/pipeline-root/"
SERVICE_ACCOUNT = "985136436720-compute@developer.gserviceaccount.com"


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--training-image-uri",
        required=True,
        help="Artifact Registry URI for the training container image.",
    )

    parser.add_argument(
        "--serving-image-uri",
        required=True,
        help="Artifact Registry URI for the serving container image.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
    )

    job = aiplatform.PipelineJob(
        display_name="hotel-cancellation-pipeline",
        template_path="hotel_pipeline.json",
        pipeline_root=PIPELINE_ROOT,
        parameter_values={
            "training_image_uri": args.training_image_uri,
            "serving_image_uri": args.serving_image_uri,
        },
    )

    job.run(
        service_account=SERVICE_ACCOUNT,
    )


if __name__ == "__main__":
    main()