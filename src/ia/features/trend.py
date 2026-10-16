from src.domain.measurement import Measurement


def calculate_inclinacao(measurements: list[Measurement],) -> float:

    if len(measurements) < 2:
        return 0.0

    first_data_hora = measurements[0].data_hora

    times_minutes = [
        (
            measurement.data_hora
            - first_data_hora
        ).total_seconds() / 60.0
        for measurement in measurements
    ]

    values = [
        measurement.value
        for measurement in measurements
    ]

    media_time = sum(times_minutes) / len(times_minutes)
    media_value = sum(values) / len(values)

    numerator = sum(
        (time - media_time)
        * (value - media_value)
        for time, value in zip(
            times_minutes,
            values,
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