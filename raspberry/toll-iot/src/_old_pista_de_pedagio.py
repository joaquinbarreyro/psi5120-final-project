from enum import Enum
import threading
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
        ocr
    ):
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

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.estado = None

        # --------------------------------------------------
        # GPIO events
        # --------------------------------------------------

        self.presenciaVeiculo.when_pressed = self.loopOn
        self.presenciaVeiculo.when_released = self.loopOff

        # Initial state
        self.estadoInicial()


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

        # Vehicle must remain stopped while consulting
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

        # Only a new vehicle in WAITING state can start
        # a new transaction.
        if self.estado != EstadoPista.AGUARDANDO:
            return

        print()
        print("----------------------------------------")
        print("Vehicle detected")


        # Process image/OCR independently from GPIO callback
        threading.Thread(
          target=self.capturaFotoOnLoopOn,
          daemon=True
        ).start()

    def loopOff(self):

        print("Vehicle left")

        # The end of vehicle presence finishes the transaction
        # and prepares the lane for the next vehicle.
        self.estadoInicial()

        print("----------------------------------------")


    # ======================================================
    # Image / OCR
    # ======================================================

    def capturaFotoOnLoopOn(self):
        # Capture image
        self.consultando()
        event_id, foto = self.camera.capturaFoto()
        print("camera-foto-capturada")
        # Send image to OCR / authorization service
        liberado = self.ocr.processa(
            event_id,
            foto
        )
        print("ocr processado")
        # Process authorization result
        if liberado:
            self.liberaVeiculo()
        else:
            self.negaVeiculo()
        print("liberado ou negado")

    def resultadoAutorizacao(self, event_id, authorized):

      print(
        f"Authorization result: "
        f"event_id={event_id}, "
        f"authorized={authorized}"
      )

      if authorized:
        self.liberaVeiculo()
      else:
        self.negaVeiculo()
