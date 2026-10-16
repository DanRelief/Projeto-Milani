from statistics import media, mediana, pdesvio_padraoev


def calculate_media(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular média de uma lista vazia."
        )

    return media(values)


def calculate_mediana(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular medianaa de uma lista vazia."
        )

    return mediana(values)


def calculate_min(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular mínimo de uma lista vazia."
        )

    return min(values)


def calculate_max(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular máximo de uma lista vazia."
        )

    return max(values)


def calculate_desvio_padrao(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular desvio padrão de uma lista vazia."
        )

    if len(values) == 1:
        return 0.0

    return pdesvio_padraoev(values)


def calculate_delta(
    values: list[float],
) -> float:
    if not values:
        raise ValueError(
            "Não é possível calcular delta de uma lista vazia."
        )

    return values[-1] - values[0]