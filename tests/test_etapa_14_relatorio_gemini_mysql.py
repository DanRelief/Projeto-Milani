from src.ia.llm.construtor_contexto import (
    ConstrutorContextoRelatorio,
)

from src.ia.llm.construtor_prompt import (
    construir_prompt_relatorio,
)

from src.ia.llm.gemini_client import (
    GeminiClient,
)


ID_SESSAO_TESTE = (
    "ec6e5290-a80f-4914-9086-f5da563eff13"
)


def test_relatorio_gemini_com_sessao_real():

    construtor_contexto = (
        ConstrutorContextoRelatorio()
    )

    contexto = (
        construtor_contexto.construir(
            id_sessao=ID_SESSAO_TESTE
        )
    )

    assert contexto.paciente is not None

    assert len(
        contexto.resumo_sinais
    ) > 0

    prompt = (
        construir_prompt_relatorio(
            contexto
        )
    )

    assert contexto.paciente.nome in prompt

    cliente = GeminiClient()

    relatorio = (
        cliente.gerar_relatorio(
            prompt
        )
    )

    assert relatorio.resumo_geral

    assert isinstance(
        relatorio.evolucao_sinais,
        list,
    )

    assert isinstance(
        relatorio.eventos_relevantes,
        list,
    )

    assert isinstance(
        relatorio.relacoes_temporais,
        list,
    )

    assert isinstance(
        relatorio.informacoes_ausentes,
        list,
    )

    assert relatorio.aviso

    print()
    print(
        "RELATÓRIO GEMINI - SESSÃO REAL"
    )
    print(
        "============================="
    )

    print()
    print(
        "Paciente:",
        contexto.paciente.nome,
    )

    print(
        "Sessão:",
        contexto.sessao.id_sessao,
    )

    print()
    print(
        "RESUMO GERAL"
    )
    print(
        relatorio.resumo_geral
    )

    print()
    print(
        "EVOLUÇÃO DOS SINAIS"
    )

    for item in (
        relatorio.evolucao_sinais
    ):
        print(
            "-",
            item,
        )

    print()
    print(
        "EVENTOS RELEVANTES"
    )

    for item in (
        relatorio.eventos_relevantes
    ):
        print(
            "-",
            item,
        )

    print()
    print(
        "RELAÇÕES TEMPORAIS"
    )

    for item in (
        relatorio.relacoes_temporais
    ):
        print(
            "-",
            item,
        )

    print()
    print(
        "INFORMAÇÕES AUSENTES"
    )

    for item in (
        relatorio.informacoes_ausentes
    ):
        print(
            "-",
            item,
        )

    print()
    print(
        "OBSERVAÇÕES"
    )

    for item in (
        relatorio.observacoes
    ):
        print(
            "-",
            item,
        )

    print()
    print(
        "AVISO"
    )
    print(
        relatorio.aviso
    )