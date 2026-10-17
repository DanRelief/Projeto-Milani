def criar_vetor_caracteristicas(caracteristicas,) -> list[float]:

    return [
        float(caracteristicas.valor_atual),

        float(caracteristicas.media),

        float(caracteristicas.mediana),

        float(caracteristicas.minimo),

        float(caracteristicas.maximo),

        float(caracteristicas.desvio_padrao),

        float(caracteristicas.delta),

        float(caracteristicas.inclinacao),
    ]