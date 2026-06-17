from google.cloud import aiplatform

PROJECT_ID = "burner-neisincl"
REGION = "us-central1"

aiplatform.init(
    project=PROJECT_ID,
    location=REGION,
)

job = aiplatform.PipelineJob(
    display_name="hotel-cancellation-pipeline",
    template_path="hotel_pipeline.json",
    pipeline_root="gs://burner-neisincl-ml-pipeline-artefacts/pipeline-root/",
)

job.run(
    service_account="985136436720-compute@developer.gserviceaccount.com"
)