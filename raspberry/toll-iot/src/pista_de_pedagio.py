from enum import Enum
import threading
import time
import csv
from pathlib import Path
from gpiozero import Button, LED


class EstadoPista(Enum):
    AGUARDANDO = 1
    CONSULTANDO = 2
    LIBERADO = 3
    NEGADO = 4


class PistaDePedagio:

    def __init__(
        self,
        gpio_loop,
        gpio_verde,
        gpio_vermelho,
        gpio_amarelo,
        camera,
        ocr,
        s3,
        log_file
     ):
        #-----------------------------
        #arquivo para salvar dados de tempo
        #----------------------------------
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


        # --------------------------------------------------
        # Input
        # --------------------------------------------------
       
        self.presenciaVeiculo = Button(
            gpio_loop,
            pull_up=False
        )

        # --------------------------------------------------
        # Outputs
        # --------------------------------------------------

        self.semaforoVerde = LED(gpio_verde)
        self.semaforoVermelho = LED(gpio_vermelho)
        self.semaforoAmarelo = LED(gpio_amarelo)

        # --------------------------------------------------
        # Services
        # --------------------------------------------------

        self.camera = camera
        self.ocr = ocr
        self.s3 = s3

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.estado = None
        self.event_id_atual = None

        # --------------------------------------------------
        # GPIO events
        # --------------------------------------------------

        self.presenciaVeiculo.when_pressed = self.loopOn
        self.presenciaVeiculo.when_released = self.loopOff

        self.estadoInicial()


    #-------------------------
    # salvar os resultados/tempos  obtidos em cada teste
    #-------------------------- 
    def salvaResultado(
	    self,
	    event_id,
	    plate,
	    authorized,
	    rekognition_ms,
	    dynamodb_ms,
	    lambda_processing_ms,
	    e2e_ms
	):
	    arquivo_novo = not self.log_file.exists()

	    with self.log_file.open("a", newline="") as f:
	        writer = csv.writer(f)

	        if arquivo_novo:
	            writer.writerow([
	                "event_id",
	                "plate",
	                "authorized",
	                "capture_ms",
	                "upload_ms",
	                "rekognition_ms",
	                "dynamodb_ms",
	                "lambda_processing_ms",
	                "e2e_ms"
	            ])

	        writer.writerow([
	            event_id,
	            plate,
	            authorized,
	            round(self.capture_ms, 2),
	            round(self.upload_ms, 2),
	            round(rekognition_ms, 2),
	            round(dynamodb_ms, 2),
	            round(lambda_processing_ms, 2),
	            round(e2e_ms, 2)
	        ])

    # ======================================================
    # States
    # ======================================================

    def estadoInicial(self):

        self.estado = EstadoPista.AGUARDANDO

        self.semaforoVermelho.on()
        self.semaforoAmarelo.off()
        self.semaforoVerde.off()

        print("State: WAITING")


    def consultando(self):

        self.estado = EstadoPista.CONSULTANDO

        self.semaforoVermelho.on()
        self.semaforoAmarelo.on()
        self.semaforoVerde.off()

        print("State: CONSULTING")


    def liberaVeiculo(self):

        self.estado = EstadoPista.LIBERADO

        self.semaforoVermelho.off()
        self.semaforoAmarelo.off()
        self.semaforoVerde.on()

        print("State: AUTHORIZED")


    def negaVeiculo(self):

        self.estado = EstadoPista.NEGADO

        self.semaforoVermelho.on()
        self.semaforoAmarelo.off()
        self.semaforoVerde.off()

        print("State: DENIED")


    # ======================================================
    # Loop events
    # ======================================================

    def loopOn(self):
        if self.estado != EstadoPista.AGUARDANDO:
            return

        self.t0_ns = time.monotonic_ns()
        print()
        print("----------------------------------------")
        print("Vehicle detected")

        self.consultando()

        threading.Thread(
            target=self.capturaFotoOnLoopOn,
            daemon=True
        ).start()


    def loopOff(self):

        print("Vehicle left")

        # Invalidate current transaction
        self.event_id_atual = None

        self.estadoInicial()

        print("----------------------------------------")


    # ======================================================
    # Image acquisition
    # ======================================================

    def capturaFotoOnLoopOn(self):
      try:
        #capture  
        t0_ns = time.monotonic_ns()
        event_id, foto = self.camera.capturaFoto()
        t1_ns = time.monotonic_ns()
        self.capture_ms = (t1_ns - t0_ns) / 1_000_000
        
        self.event_id_atual = event_id

        print("Image captured")
        print(f"Current event ID: {event_id}")
    
        t0_ns = time.monotonic_ns()
        # Upload image to cloud
        self.s3.upload(
            image_path=foto,
            event_id=event_id
        )
        t1_ns = time.monotonic_ns()
        self.upload_ms = (t1_ns - t0_ns) / 1_000_000
        print(f"Upload time: {self.upload_ms:.2f} ms")
        print("Waiting for cloud authorization...")
      except Exception as e:
        print(f"Transaction error: {e}")
        self.negaVeiculo()

    # ======================================================
    # Cloud authorization result
    # ======================================================

    def resultadoAutorizacao(self, event_id, plate,authorized, rekognition_ms, dynamodb_ms, lambda_processing_ms):

        print()
        print(
            f"Authorization result received: "
            f"event_id={event_id}, "
            f"plate={plate}, "
            f"authorized={authorized}",
            f"rekognition_ms={rekognition_ms}",
            f"dynamodb_ms={dynamodb_ms}",
            f"lambda_processing_ms={lambda_processing_ms}"
        )

        # Ignore response if there is no vehicle
        if not self.presenciaVeiculo.is_pressed:
            print("Result ignored: no vehicle present.")
            return

        # Ignore response if lane is no longer consulting
        if self.estado != EstadoPista.CONSULTANDO:
            print("Result ignored: lane is not consulting.")
            return

        # Ignore response from another transaction
        if event_id != self.event_id_atual:
            print(
                f"Result ignored: event ID mismatch "
                f"(expected {self.event_id_atual})."
            )
            return

        if authorized:
            self.liberaVeiculo()
        else:
            self.negaVeiculo()

       	t8_ns = time.monotonic_ns()
       	e2e_ms = (t8_ns - self.t0_ns) / 1_000_000

        print(f"End-to-end time: {e2e_ms:.2f} ms")


        self.salvaResultado(
	      event_id=event_id,
	      plate=plate,
	      authorized=authorized,
	      rekognition_ms=rekognition_ms,
	      dynamodb_ms=dynamodb_ms,
	      lambda_processing_ms=lambda_processing_ms,
	      e2e_ms=e2e_ms
	    )
