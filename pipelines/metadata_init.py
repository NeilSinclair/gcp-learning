from google.cloud import aiplatform

aiplatform.init(
    project="burner-neisincl",
    location="us-central1",
    experiment="hotel-cancellation-init",
)

print("Initialized Vertex experiment / metadata.")