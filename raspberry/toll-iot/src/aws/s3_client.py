from pathlib import Path

import boto3


class S3Client:

    def __init__(self, bucket, profile, region="us-east-1"):

        self.bucket = bucket

        session = boto3.Session(
            profile_name=profile,
            region_name=region
        )

        self.s3 = session.client("s3")


    def upload(self, image_path, event_id):

        image_path = Path(image_path)

        object_key = f"{event_id}.jpg"

        print(f"Uploading image to S3: {object_key}")

        self.s3.upload_file(
            str(image_path),
            self.bucket,
            object_key
        )

        print(f"S3 upload complete: s3://{self.bucket}/{object_key}")

        return object_key
