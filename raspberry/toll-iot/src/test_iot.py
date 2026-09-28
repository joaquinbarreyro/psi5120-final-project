from pathlib import Path

from aws.iot_client import IoTClient


BASE_DIR = Path.home() / "toll-iot"
CERT_DIR = BASE_DIR / "certs"

ENDPOINT = "a30gny2bzdk8l7-ats.iot.us-east-1.amazonaws.com"

TOPIC = "toll/result/psi5120-toll-raspberry"


def resultadoAutorizacao(event_id, authorized):

    print()
    print("----------------------------------------")
    print("Application callback")
    print(f"Event ID:   {event_id}")
    print(f"Authorized: {authorized}")
    print("----------------------------------------")


iot = IoTClient(
    endpoint=ENDPOINT,
    client_id="psi5120-toll-raspberry",
    cert_path=CERT_DIR / "psi5120-toll-raspberry.cert.pem",
    key_path=CERT_DIR / "psi5120-toll-raspberry.private.key",
    ca_path=CERT_DIR / "AmazonRootCA1.pem"
)

try:

    iot.conecta()

    iot.subscribeResultado(
        TOPIC,
        resultadoAutorizacao
    )

    input("Waiting for MQTT messages. Press ENTER to exit...")

finally:

    iot.desconecta()
