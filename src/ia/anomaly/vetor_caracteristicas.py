def criar_vetor_caracteristicas(caracteristicas,) -> list[float]:

    return [
        caracteristicas.valor_atual,
        caracteristicas.media,
        caracteristicas.mediana,
        caracteristicas.minimo,
        caracteristicas.maximo,
        caracteristicas.desvio_padrao,
        caracteristicas.delta,
        caracteristicas.inclinacao,
    ]


def criar_vetor_relativo(caracteristicas,) -> list[float]:

    referencia = (
        caracteristicas.mediana
    )

    if referencia == 0:
        raise ValueError(
            "Não é possível criar o vetor "
            "relativo com mediana igual a zero."
        )

    desvio_atual_relativo = (
        (
            caracteristicas.valor_atual
            - caracteristicas.mediana
        )
        / referencia
    )

    amplitude_relativa = (
        (
            caracteristicas.maximo
            - caracteristicas.minimo
        )
        / referencia
    )

    variabilidade_relativa = (
        caracteristicas.desvio_padrao
        / referencia
    )

    delta_relativo = (
        caracteristicas.delta
        / referencia
    )

    inclinacao_relativa = (
        caracteristicas.inclinacao
        / referencia
    )

    return [
        desvio_atual_relativo,
        amplitude_relativa,
        variabilidade_relativa,
        delta_relativo,
        inclinacao_relativa,
    ]