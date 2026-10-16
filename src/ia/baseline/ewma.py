from dataclasses import dataclass


@dataclass
class ResultadoEWMA:
    valor_atual: float
    ewma_atual: float
    diferenca: float
    alfa: float


def calcular_serie_ewma(
    valores: list[float],
    alfa: float = 0.2,
) -> list[float]:

    if not valores:
        raise ValueError(
            "Não é possível calcular EWMA "
            "de uma lista vazia."
        )

    if not 0.0 < alfa <= 1.0:
        raise ValueError(
            "alfa deve estar entre 0 e 1."
        )

    serie_ewma = [
        valores[0]
    ]

    for valor in valores[1:]:

        ewma_anterior = serie_ewma[-1]

        ewma_atual = (
            alfa * valor
            + (1.0 - alfa) * ewma_anterior
        )

        serie_ewma.append(
            ewma_atual
        )

    return serie_ewma

def calcular_ewma_atual(
    valores: list[float],
    alfa: float = 0.2,
) -> ResultadoEWMA:

    serie_ewma = calcular_serie_ewma(
        valores=valores,
        alfa=alfa,
    )

    valor_atual = valores[-1]
    ewma_atual = serie_ewma[-1]

    return ResultadoEWMA(
        valor_atual=valor_atual,
        ewma_atual=ewma_atual,
        diferenca=(
            valor_atual - ewma_atual
        ),
        alfa=alfa,
    )