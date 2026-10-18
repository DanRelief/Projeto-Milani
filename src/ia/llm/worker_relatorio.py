from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from src.ia.llm.report_service import (
    ServicoRelatorio,
)


class WorkerRelatorio(QObject):

    relatorio_gerado = Signal(object)

    erro = Signal(str)

    finalizado = Signal()

    def __init__(
        self,
        id_sessao: str,
        analises_atuais: dict | None = None,
        servico_relatorio=None,
    ) -> None:

        super().__init__()

        self.id_sessao = id_sessao

        self.analises_atuais = (
            analises_atuais
        )

        self.servico_relatorio = (
            servico_relatorio
            if servico_relatorio is not None
            else ServicoRelatorio()
        )

    @Slot()
    def executar(self) -> None:

        try:
            relatorio = (
                self.servico_relatorio.gerar(
                    id_sessao=(
                        self.id_sessao
                    ),
                    analises_atuais=(
                        self.analises_atuais
                    ),
                )
            )

            self.relatorio_gerado.emit(
                relatorio
            )

        except Exception as erro:

            self.erro.emit(
                str(erro)
            )

        finally:

            self.finalizado.emit()