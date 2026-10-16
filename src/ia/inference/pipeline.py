class InferencePipeline:
    """Ponto de entrada para o processamento de novas medições."""

    def process(self, medicao):
        raise NotImplementedError(
            "O pipeline de inferência ainda não foi implementado."
        )
