import json
import re
import time
import urllib.parse
from pathlib import Path
import boto3


rekognition = boto3.client("rekognition")
dynamodb = boto3.resource("dynamodb")
plate_table = dynamodb.Table("plateList")
iot = boto3.client(
    "iot-data",
    region_name="us-east-1"
)

RESULT_TOPIC = "toll/result/psi5120-toll-raspberry"

def normalize_plate(text):

    plate = normalize_text(text)

    old_pattern = r"^[A-Z]{3}[0-9]{4}$"
    mercosul_pattern = r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$"

    if re.match(old_pattern, plate):
        return plate

    if re.match(mercosul_pattern, plate):
        return plate

    return None

def normalize_text(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())



def find_plate(text_detections):

    # Brazilian Mercosul format:
    # AAA1A11
    plate_pattern = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")

    for detection in text_detections:

        if detection["Type"] != "LINE":
            continue

        text = detection["DetectedText"]
        confidence = detection["Confidence"]

        normalized = normalize_text(text)
        plate = normalize_plate(text)
        print(
            f"LINE: {text} "
            f"-> {normalized} "
            f"(confidence={confidence:.2f}%)"
        )

        if plate is not None:
            return plate, confidence


    return None, None


def lambda_handler(event, context):
    lambda_start_ns = time.perf_counter_ns()
    
    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]

    object_key = urllib.parse.unquote_plus(
        record["s3"]["object"]["key"]
    )

    event_id = Path(object_key).stem

    print("----------------------------------------")
    print(f"Bucket:   {bucket}")
    print(f"Object:   {object_key}")
    print(f"Event ID: {event_id}")

    # ------------------------------------------------------
    # Rekognition
    # ------------------------------------------------------
    rekognition_start_ns = time.perf_counter_ns()
    response = rekognition.detect_text(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": object_key
            }
        }
    )
    rekognition_end_ns = time.perf_counter_ns()
    rekognition_ms = (
        rekognition_end_ns - rekognition_start_ns
    ) / 1_000_000

    plate, confidence = find_plate(
        response["TextDetections"]
    )

    # ------------------------------------------------------
    # DynamoDB
    # ------------------------------------------------------

    authorized = False

    dynamodb_ms = 0.0
    if plate is None:

        print("Plate not detected.")

    else:

        print(f"Plate detected: {plate}")
        dynamodb_start_ns = time.perf_counter_ns()
        db_response = plate_table.get_item(
            Key={
                "plate": plate
            }
        )
        dynamodb_end_ns = time.perf_counter_ns()

        item = db_response.get("Item")

        dynamodb_ms = (
            dynamodb_end_ns - dynamodb_start_ns
        ) / 1_000_000

        if item is None:

            print("Plate not found in DynamoDB.")

        else:

            authorized = bool(
                item.get("authorized", False)
            )

            print(
                f"DynamoDB result: "
                f"plate={plate}, "
                f"authorized={authorized}"
            )

    lambda_processing_ms = (
        time.perf_counter_ns() - lambda_start_ns
    ) / 1_000_000

    # ------------------------------------------------------
    # Result
    # ------------------------------------------------------

    result = {
        "event_id": event_id,
        "plate": plate,
        "authorized": authorized,
        "rekognition_ms": round(rekognition_ms, 2),
        "dynamodb_ms": round(dynamodb_ms, 2),
        "lambda_processing_ms": round(lambda_processing_ms, 2)
    }

    print("----------------------------------------")
    print("Authorization result:")
    print(json.dumps(result))
    print("----------------------------------------")

    # ------------------------------------------------------
    # AWS IoT Core
    # ------------------------------------------------------

    iot.publish(
        topic=RESULT_TOPIC,
        qos=1,
        payload=json.dumps(result)
    )

    print(f"MQTT result published: {RESULT_TOPIC}")


    return result
