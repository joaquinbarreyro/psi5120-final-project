class OCR:

    def __init__(self):
        self.numeroRequisicao = 0


    def processa(self, event_id, image_path):

        self.numeroRequisicao += 1

        print(
            f"OCR request #{self.numeroRequisicao} "
            f"- Event: {event_id}"
        )

        if self.numeroRequisicao % 2 == 0:
            print("OCR result: AUTHORIZED")
            return True

        print("OCR result: DENIED")
        return False
