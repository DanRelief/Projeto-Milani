from dataclasses import dataclass
from statistics import mediana
from src.domain.measurement import Measurement, Vitalparametro


@dataclass
class BaselineStats:
    parametro: Vitalparametro

    count: int

    mediana: float
    mad: float

    start_data_hora: object
    end_data_hora: object


def calculate_mad(values: list[float],mediana_value: float | None = None,) -> float:

    if not values:
        raise ValueError(
            "Não é possível calcular MAD "
            "de uma lista vazia."
        )

    if mediana_value is None:
        mediana_value = mediana(values)

    absolute_deviations = [
        abs(value - mediana_value)
        for value in values
    ]

    return mediana(
        absolute_deviations
    )

def calculate_rolling_baseline(measurements: list[Measurement],exclude_valor_atual: bool = True,minimo_samples: int = 5) -> BaselineStats:

    if not measurements:
        raise ValueError(
            "Não há medições para calcular baseline."
        )

    parametro = measurements[0].parametro

    for measurement in measurements:
        if measurement.parametro != parametro:
            raise ValueError(
                "Todas as medições devem pertencer "
                "ao mesmo parâmetro."
            )

    baseline_measurements = measurements

    if exclude_valor_atual:
        baseline_measurements = measurements[:-1]

    if len(baseline_measurements) < minimo_samples:
        raise ValueError(
            f"Baseline requer pelo menos "
            f"{minimo_samples} medições."
        )

    values = [
        measurement.value
        for measurement in baseline_measurements
    ]

    mediana_value = mediana(values)

    mad_value = calculate_mad(
        values,
        mediana_value=mediana_value,
    )

    return BaselineStats(
        parametro=parametro,

        count=len(values),

        mediana=mediana_value,
        mad=mad_value,

        start_data_hora=(
            baseline_measurements[0].data_hora
        ),

        end_data_hora=(
            baseline_measurements[-1].data_hora
        ),
    )