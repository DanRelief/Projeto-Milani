from src.domain.measurement import Medicao


def calculate_inclinacao(measurements: list[Medicao],) -> float:

    if len(measurements) < 2:
        return 0.0

    first_data_hora = measurements[0].data_hora

    times_minutes = [
        (
            Medicao.data_hora
            - first_data_hora
        ).total_seconds() / 60.0
        for Medicao in measurements
    ]

    valors = [
        Medicao.valor
        for Medicao in measurements
    ]

    media_time = sum(times_minutes) / len(times_minutes)
    media_valor = sum(valors) / len(valors)

    numerator = sum(
        (time - media_time)
        * (valor - media_valor)
        for time, valor in zip(
            times_minutes,
            valors,
        )
    )

    denominator = sum(
        (time - media_time) ** 2
        for time in times_minutes
    )

    if denominator == 0:
        return 0.0

    inclinacao = numerator / denominator

    return inclinacao