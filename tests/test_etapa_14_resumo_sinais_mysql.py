from src.ia.llm.construtor_contexto import (
    ConstrutorContextoRelatorio,
)


ID_SESSAO_TESTE = (
    "ec6e5290-a80f-4914-9086-f5da563eff13"
)


def test_resumo_estatistico_sinais():

    construtor = (
        ConstrutorContextoRelatorio()
    )

    contexto = construtor.construir(
        id_sessao=ID_SESSAO_TESTE
    )

    resumos = contexto.resumo_sinais

    assert len(resumos) == 3

    parametros = {
        resumo.parametro
        for resumo in resumos
    }

    assert "spo2" in parametros

    assert (
        "temperatura"
        in parametros
    )

    assert (
        "pressao_arterial_media"
        in parametros
    )

    for resumo in resumos:

        assert (
            resumo.quantidade_medicoes
            > 0
        )

        assert (
            resumo.valor_inicial
            is not None
        )

        assert (
            resumo.valor_final
            is not None
        )

        assert (
            resumo.minimo
            <= resumo.maximo
        )

        assert (
            resumo.minimo
            <= resumo.media
            <= resumo.maximo
        )

        assert (
            resumo.minimo
            <= resumo.mediana
            <= resumo.maximo
        )

    print()
    print(
        "RESUMO DOS SINAIS VITAIS"
    )
    print(
        "========================"
    )

    for resumo in resumos:

        print()
        print(
            resumo.nome
        )

        print(
            "Medições:",
            resumo.quantidade_medicoes,
        )

        print(
            "Inicial:",
            resumo.valor_inicial,
            resumo.unidade,
        )

        print(
            "Final:",
            resumo.valor_final,
            resumo.unidade,
        )

        print(
            "Mínimo:",
            round(
                resumo.minimo,
                3,
            ),
        )

        print(
            "Máximo:",
            round(
                resumo.maximo,
                3,
            ),
        )

        print(
            "Média:",
            round(
                resumo.media,
                3,
            ),
        )

        print(
            "Mediana:",
            round(
                resumo.mediana,
                3,
            ),
        )

        print(
            "Alertas:",
            resumo.quantidade_alertas,
        )