import pytest

from src.ia.baseline.ewma import (
    calcular_ewma_atual,
    calcular_serie_ewma,
)


def test_ewma_serie_constante():

    valores = [
        98.0,
        98.0,
        98.0,
        98.0,
    ]

    resultado = calcular_serie_ewma(
        valores,
        alfa=0.2,
    )

    assert resultado == [
        98.0,
        98.0,
        98.0,
        98.0,
    ]


def test_ewma_queda_progressiva():

    valores = [
        98.0,
        98.0,
        97.0,
        96.0,
        95.0,
        94.0,
    ]

    resultado = calcular_ewma_atual(
        valores,
        alfa=0.2,
    )

    print()
    print("EWMA")
    print("----------------")
    print(
        "Valor atual:",
        resultado.valor_atual
    )
    print(
        "EWMA atual:",
        resultado.ewma_atual
    )
    print(
        "Diferença:",
        resultado.diferenca
    )

    assert resultado.valor_atual == 94.0

    assert resultado.ewma_atual > 94.0

    assert resultado.diferenca < 0


def test_alfa_invalido():

    with pytest.raises(ValueError):
        calcular_serie_ewma(
            [98.0, 97.0],
            alfa=0.0,
        )