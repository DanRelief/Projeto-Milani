from datetime import datetime, timedelta

from src.ia.baseline.rolling import (
    calculate_rolling_baseline,
)

from src.ia.baseline.robust_zscore import (
    calculate_robust_zscore,
)

from src.domain.measurement import (
    DataSource,
    Measurement,
    Vitalparametro,
)


def test_robust_zscore():

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
            Measurement(
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

                source=DataSource.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    valor_atual_value = (
        measurements[-1].value
    )

    result = calculate_robust_zscore(
        valor_atual_value=valor_atual_value,
        baseline=baseline,
    )

    print()
    print("Robust Z-Score SpO2")
    print("-------------------")

    print(
        "valor_atual:",
        result.valor_atual_value
    )

    print(
        "Baseline mediana:",
        result.baseline_mediana
    )

    print(
        "MAD:",
        result.baseline_mad
    )

    print(
        "Robust Z:",
        result.robust_zscore
    )

    print(
        "Computable:",
        result.computable
    )

    assert result.computable is True

    assert result.robust_zscore is not None

    assert result.robust_zscore < 0

def test_robust_zscore_valor_proximo_baseline():

    start = datetime(
        2026,
        10,
        15,
        10,
        0,
        0,
    )

    baseline_values = [
        98.0,
        98.1,
        97.9,
        98.0,
        98.2,
        97.8,
        98.0,
    ]

    measurements = []

    for index, value in enumerate(
        baseline_values
    ):
        measurements.append(
            Measurement(
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

                source=DataSource.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    measurements.append(
        Measurement(
            id_paciente="DOG_001",
            id_sessao="SESSION_001",

            data_hora=(
                start
                + timedelta(
                    seconds=35
                )
            ),

            parametro=Vitalparametro.SPO2,

            value=98.05,
            unit="%",

            source=DataSource.SIMULATOR,
            qualidade_sinal=1.0,
        )
    )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    result = calculate_robust_zscore(
        valor_atual_value=98.05,
        baseline=baseline,
    )

    print()
    print(
        "Robust Z normal:",
        result.robust_zscore
    )

    assert result.computable is True

    assert abs(
        result.robust_zscore
    ) < 1


def test_robust_zscore_mad_zero():

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
        98.0,
        98.0,
        98.0,
        98.0,

        94.0,
    ]

    measurements = []

    for index, value in enumerate(values):

        measurements.append(
            Measurement(
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

                source=DataSource.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    result = calculate_robust_zscore(
        valor_atual_value=94.0,
        baseline=baseline,
    )

    assert baseline.mad == 0

    assert result.computable is False

    assert result.robust_zscore is None