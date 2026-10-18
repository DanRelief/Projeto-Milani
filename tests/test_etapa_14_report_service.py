from datetime import datetime

from src.ia.llm.modelos_contexto import (
    ContextoRelatorio,
    DadosPacienteRelatorio,
    DadosResponsaveisRelatorio,
    DadosSessaoRelatorio,
)

from src.ia.llm.modelos_saida import (
    RelatorioGemini,
)

from src.ia.llm.report_service import (
    ServicoRelatorio,
)


class ConstrutorContextoFake:

    def __init__(self):
        self.id_sessao_recebido = None
        self.analises_recebidas = None

    def construir(
        self,
        id_sessao,
        analises_atuais=None,
    ):

        self.id_sessao_recebido = (
            id_sessao
        )

        self.analises_recebidas = (
            analises_atuais
        )

        return ContextoRelatorio(
            paciente=(
                DadosPacienteRelatorio(
                    id_paciente="1",
                    nome="Ana",
                    especie="Cão",
                )
            ),
            responsaveis=(
                DadosResponsaveisRelatorio(
                    responsavel_animal="Bryan",
                )
            ),
            sessao=(
                DadosSessaoRelatorio(
                    id_sessao=id_sessao,
                    inicio=datetime(
                        2026,
                        10,
                        18,
                        10,
                        0,
                    ),
                )
            ),
            data_hora_geracao=(
                datetime.now()
            ),
        )


class GeminiClientFake:

    def __init__(self):
        self.prompt_recebido = None

    def gerar_relatorio(
        self,
        prompt,
    ):

        self.prompt_recebido = prompt

        return RelatorioGemini(
            resumo_geral=(
                "Sessão analisada."
            ),
            evolucao_sinais=[],
            eventos_relevantes=[],
            relacoes_temporais=[],
            informacoes_ausentes=[],
            observacoes=[],
            aviso=(
                "Relatório de apoio à "
                "interpretação veterinária."
            ),
        )


def test_servico_relatorio_orquestra_fluxo():

    construtor_fake = (
        ConstrutorContextoFake()
    )

    gemini_fake = (
        GeminiClientFake()
    )

    servico = ServicoRelatorio(
        construtor_contexto=(
            construtor_fake
        ),
        cliente_gemini=(
            gemini_fake
        ),
    )

    relatorio = servico.gerar(
        id_sessao="SESSAO_TESTE"
    )

    assert (
        construtor_fake
        .id_sessao_recebido
        == "SESSAO_TESTE"
    )

    assert (
        gemini_fake.prompt_recebido
        is not None
    )

    assert (
        "Ana"
        in gemini_fake.prompt_recebido
    )

    assert (
        relatorio.resumo_geral
        == "Sessão analisada."
    )

    print()
    print(
        "REPORT SERVICE"
    )
    print(
        "=============="
    )

    print(
        "Sessão recebida:",
        construtor_fake.id_sessao_recebido,
    )

    print(
        "Prompt enviado:",
        bool(
            gemini_fake.prompt_recebido
        ),
    )

    print(
        "Resumo:",
        relatorio.resumo_geral,
    )