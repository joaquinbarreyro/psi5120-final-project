#!/usr/bin/env python3

from pathlib import Path
from signal import pause

from camera import Camera
from ocr import OCR
from pista_de_pedagio import PistaDePedagio
from aws.iot_client import IoTClient
from aws.s3_client import S3Client

# ==========================================================
# Configuration
# ==========================================================

BASE_DIR = Path.home() / "toll-iot"
IMAGE_DIR = BASE_DIR / "images"
LOG_FILE = BASE_DIR / "logs" / "results.csv"

CAMERA_DEVICE = "/dev/video0"
CAMERA_RESOLUTION = "1280x720"

GPIO_LOOP = 17
GPIO_LED_VERDE = 27
GPIO_LED_VERMELHO = 10
GPIO_LED_AMARELO = 9

AWS_REGION = "us-east-1"
AWS_PROFILE = "psi5120-toll"
S3_BUCKET = "psi5120-toll-captures"
# ==========================================================
# AWS IoT Core
# ==========================================================

CERT_DIR = BASE_DIR / "certs"

AWS_IOT_ENDPOINT = "a30gny2bzdk8l7-ats.iot.us-east-1.amazonaws.com"
AWS_IOT_CLIENT_ID = "psi5120-toll-raspberry"
AWS_IOT_RESULT_TOPIC = "toll/result/psi5120-toll-raspberry"


# ==========================================================
# Main
# ==========================================================

def main():

    print("========================================")
    print(" Electronic Toll Collection")
    print(" Raspberry Pi Roadside Prototype")
    print("========================================")

    # ------------------------------------------------------
    # Camera
    # ------------------------------------------------------

    camera = Camera(
        image_dir=IMAGE_DIR,
        device=CAMERA_DEVICE,
        resolution=CAMERA_RESOLUTION
    )

    # ------------------------------------------------------
    # OCR / authorization service
    # ------------------------------------------------------

    # For now this is the test implementation:
    #
    # odd request  -> DENIED
    # even request -> AUTHORIZED

    ocr = OCR()



    # ------------------------------------------------------
    # Amazon S3
    # ------------------------------------------------------

    s3 = S3Client(
      bucket=S3_BUCKET,
      profile=AWS_PROFILE,
      region=AWS_REGION
    )

    # ------------------------------------------------------
    # Toll lane
    # ------------------------------------------------------

    pista = PistaDePedagio(
        gpio_loop=GPIO_LOOP,
        gpio_verde=GPIO_LED_VERDE,
        gpio_vermelho=GPIO_LED_VERMELHO,
        gpio_amarelo=GPIO_LED_AMARELO,
        camera=camera,
        ocr=ocr,
        s3=s3,
        log_file=LOG_FILE
    )
# ------------------------------------------------------
# AWS IoT Core
# ------------------------------------------------------

    iot = IoTClient(
      endpoint=AWS_IOT_ENDPOINT,
      client_id=AWS_IOT_CLIENT_ID,
      cert_path=CERT_DIR / "psi5120-toll-raspberry.cert.pem",
      key_path=CERT_DIR / "psi5120-toll-raspberry.private.key",
      ca_path=CERT_DIR / "AmazonRootCA1.pem"
    )

    iot.conecta()

    iot.subscribeResultado(
      AWS_IOT_RESULT_TOPIC,
      pista.resultadoAutorizacao
    )
    # ------------------------------------------------------
    # Ready
    # ------------------------------------------------------

    print()
    print(f"Camera: {CAMERA_DEVICE}")
    print(f"Resolution: {CAMERA_RESOLUTION}")
    print()
    print(f"Loop:       GPIO{GPIO_LOOP}")
    print(f"Green LED:  GPIO{GPIO_LED_VERDE}")
    print(f"Yellow LED: GPIO{GPIO_LED_AMARELO}")
    print(f"Red LED:    GPIO{GPIO_LED_VERMELHO}")
    print()
    print("System ready.")
    print("Waiting for vehicle...")
    print()

    # Keep application running
    try:
        pause()

    except KeyboardInterrupt:
        print()
        print("Stopping system...")

    finally:
        
        iot.desconecta()
        # Safe state when application finishes
        
        pista.estadoInicial()
            
        print("System stopped.")


# ==========================================================
# Entry point
# ==========================================================

if __name__ == "__main__":
    main()
