import json

from awscrt import mqtt
from awsiot import mqtt_connection_builder


class IoTClient:

    def __init__(
        self,
        endpoint,
        client_id,
        cert_path,
        key_path,
        ca_path
    ):
        self.endpoint = endpoint
        self.client_id = client_id
        self.conectado = False

        self.connection = mqtt_connection_builder.mtls_from_path(
            endpoint=endpoint,
            cert_filepath=str(cert_path),
            pri_key_filepath=str(key_path),
            ca_filepath=str(ca_path),
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=30
        )

    def conecta(self):

        print("Connecting to AWS IoT Core...")

        connect_future = self.connection.connect()
        connect_future.result()

        self.conectado = True

        print("Connected to AWS IoT Core.")

    def desconecta(self):

        if not self.conectado:
            return

        print("Disconnecting from AWS IoT Core...")

        disconnect_future = self.connection.disconnect()
        disconnect_future.result()

        self.conectado = False

        print("Disconnected from AWS IoT Core.")

    def subscribeResultado(self, topic, callback):

        def mensagemRecebida(topic, payload, **kwargs):

            try:
                mensagem = json.loads(
                    payload.decode("utf-8")
                )

                event_id = mensagem["event_id"]
                plate = mensagem["plate"]
                authorized = mensagem["authorized"]
                rekognition_ms = mensagem["rekognition_ms"]
                dynamodb_ms = mensagem["dynamodb_ms"] 
                lambda_processing_ms = mensagem["lambda_processing_ms"] 

                print(
                    f"Authorization result received: "
                    f"event_id={event_id}, "
                    f"authorized={authorized}"
                )

                callback(
                    event_id,
                    plate,
                    authorized,
                    rekognition_ms,
                    dynamodb_ms,
                    lambda_processing_ms
                )

            except Exception as e:
                print(f"Invalid MQTT message: {e}")

        print(f"Subscribing to topic: {topic}")

        subscribe_future, _ = self.connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=mensagemRecebida
        )

        subscribe_future.result()

        print("Subscription active.")
