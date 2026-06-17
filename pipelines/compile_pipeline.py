from kfp import compiler
from hotel_pipeline import hotel_pipeline

compiler.Compiler().compile(
    pipeline_func=hotel_pipeline,
    package_path="hotel_pipeline.json",
)