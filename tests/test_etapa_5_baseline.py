from datetime import datetime, timedelta

from src.ia.baseline.rolling import (
    calculate_rolling_baseline,
)
from src.domain.measurement import (
    FonteDados,
    Medicao,
    Vitalparametro,
)


def test_rolling_mediana_e_mad():

    start = datetime(
        2026,
        10,
        15,
        10,
        0,
        0,
    )

    values = [
        98.0,
        98.1,
        97.9,
        98.0,
        98.2,
        97.8,
        98.0,

        # valor atual
        94.0,
    ]

    measurements = []

    for index, value in enumerate(values):

        measurements.append(
            Medicao(
                id_paciente="DOG_001",
                id_sessao="SESSION_001",

                data_hora=(
                    start
                    + timedelta(
                        seconds=index * 5
                    )
                ),

                parametro=Vitalparametro.SPO2,

                value=value,
                unit="%",

                source=FonteDados.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    print()
    print("Baseline SpO2")
    print("----------------")

    print("Count:", baseline.count)
    print("mediana:", baseline.mediana)
    print("MAD:", baseline.mad)

    assert baseline.count == 7
    assert baseline.mediana == 98.0
    assert round(
        baseline.mad,
        2
    ) == 0.1