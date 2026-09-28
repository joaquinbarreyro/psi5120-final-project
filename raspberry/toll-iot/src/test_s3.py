from pathlib import Path

from aws.s3_client import S3Client


BASE_DIR = Path.home() / "toll-iot"

s3 = S3Client(
    bucket="psi5120-toll-captures",
    profile="psi5120-toll",
    region="us-east-1"
)

event_id = "20260923_234633_176427"

image_path = (
    BASE_DIR
    / "images"
    / f"{event_id}.jpg"
)

s3.upload(
    image_path=image_path,
    event_id=event_id
)
