from src.ia.llm.gemini_client import (
    GeminiClient,
)


def test_gemini_retorna_relatorio_estruturado():

    cliente = GeminiClient()

    prompt = """
    Você recebeu os seguintes dados de uma sessão
    veterinária simulada.

    Paciente:
    Nome: Ana
    Espécie: Cão

    Sinais:
    SpO2:
    inicial 98%
    final 93%
    mínima 93%
    houve 1 alerta.

    Temperatura:
    permaneceu aproximadamente estável em 37,5 °C.

    PAM:
    permaneceu aproximadamente estável em 85 mmHg.

    Houve uma medicação registrada:
    Dipirona 15 mg.

    Gere um resumo estritamente baseado nesses dados.

    Não faça diagnóstico.
    Não prescreva tratamento.
    Não invente informações.
    Não afirme causalidade entre a medicação e
    a alteração da SpO2.
    """

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

    assert relatorio.aviso

    print()
    print(
        "RELATÓRIO GEMINI"
    )
    print(
        "==============="
    )

    print()
    print(
        "Resumo:"
    )
    print(
        relatorio.resumo_geral
    )

    print()
    print(
        "Evolução:"
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
        "Eventos:"
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
        "Aviso:"
    )
    print(
        relatorio.aviso
    )