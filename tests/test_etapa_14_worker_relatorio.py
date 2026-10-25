from src.ia.llm.modelos_saida import (
    RelatorioGemini,
)

from src.ia.llm.worker_relatorio import (
    WorkerRelatorio,
)


class ServicoRelatorioFake:

    def __init__(self):

        self.id_sessao_recebido = None

    def gerar(
        self,
        id_sessao,
        analises_atuais=None,
    ):

        self.id_sessao_recebido = (
            id_sessao
        )

        return RelatorioGemini(
            resumo_geral=(
                "Relatório gerado."
            ),
            evolucao_sinais=[],
            eventos_relevantes=[],
            relacoes_temporais=[],
            informacoes_ausentes=[],
            observacoes=[],
            aviso=(
                "Relatório de apoio."
            ),
        )


def test_worker_gera_relatorio(
    qtbot,
):

    servico_fake = (
        ServicoRelatorioFake()
    )

    worker = WorkerRelatorio(
        id_sessao="SESSAO_TESTE",
        servico_relatorio=(
            servico_fake
        ),
    )

    relatorios_recebidos = []

    erros_recebidos = []

    worker.relatorio_gerado.connect(
        relatorios_recebidos.append
    )

    worker.erro.connect(
        erros_recebidos.append
    )

    worker.executar()

    assert (
        servico_fake.id_sessao_recebido
        == "SESSAO_TESTE"
    )

    assert len(
        relatorios_recebidos
    ) == 1

    assert not erros_recebidos

    assert (
        relatorios_recebidos[0]
        .resumo_geral
        == "Relatório gerado."
    )

    print()
    print(
        "WORKER RELATÓRIO"
    )
    print(
        "================"
    )

    print(
        "Sessão:",
        servico_fake.id_sessao_recebido,
    )

    print(
        "Relatório:",
        relatorios_recebidos[
            0
        ].resumo_geral,
    )