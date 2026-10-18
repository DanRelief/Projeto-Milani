from datetime import datetime, timedelta

from src.domain.measurement import (
    FonteDados,
    Medicao,
    ParametroVital,
)

from src.ia.baseline.rolling import (
    BaselineStats,
    calculate_rolling_baseline,
)

from src.ia.baseline.robust_zscore import (
    calculate_robust_zscore,
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

    valors = [
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

    for index, valor in enumerate(valors):

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

                parametro=ParametroVital.SPO2,

                valor=valor,
                unidade="%",

                fonte=FonteDados.SIMULADOR,
                qualidade_sinal=1.0,
            )
        )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    valor_atual_valor = (
        measurements[-1].valor
    )

    result = calculate_robust_zscore(
        valor_atual_valor=valor_atual_valor,
        baseline=baseline,
    )

    print()
    print("Robust Z-Score SpO2")
    print("-------------------")

    print(
        "valor_atual:",
        result.valor_atual_valor
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

    baseline_valors = [
        98.0,
        98.1,
        97.9,
        98.0,
        98.2,
        97.8,
        98.0,
    ]

    measurements = []

    for index, valor in enumerate(
        baseline_valors
    ):
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

                parametro=ParametroVital.SPO2,
                valor=valor,
                unidade="%",

                fonte=FonteDados.SIMULADOR,
                qualidade_sinal=1.0,
            )
        )

    measurements.append(
        Medicao(
            id_paciente="DOG_001",
            id_sessao="SESSION_001",

            data_hora=(
                start
                + timedelta(
                    seconds=35
                )
            ),

            parametro=ParametroVital.SPO2,

            valor=98.05,
            unidade="%",

            fonte=FonteDados.SIMULADOR,
            qualidade_sinal=1.0,
        )
    )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    result = calculate_robust_zscore(
        valor_atual_valor=98.05,
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

    valors = [
        98.0,
        98.0,
        98.0,
        98.0,
        98.0,

        94.0,
    ]

    measurements = []

    for index, valor in enumerate(valors):

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

                parametro=ParametroVital.SPO2,
                valor=valor,
                unidade="%",

                fonte=FonteDados.SIMULADOR,
                qualidade_sinal=1.0,
            )
        )

    baseline = calculate_rolling_baseline(
        measurements,
        exclude_valor_atual=True,
        minimo_samples=5,
    )

    result = calculate_robust_zscore(
        valor_atual_valor=94.0,
        baseline=baseline,
    )

    assert baseline.mad == 0

    assert result.computable is False

    assert result.robust_zscore is None

def criar_baseline_teste(
    parametro: ParametroVital,
    mediana: float,
    mad: float,
) -> BaselineStats:

    inicio = datetime(
        2026,
        10,
        18,
        10,
        0,
        0,
    )

    fim = datetime(
        2026,
        10,
        18,
        10,
        1,
        0,
    )

    return BaselineStats(
        parametro=parametro,
        count=5,
        mediana=mediana,
        mad=mad,
        start_data_hora=inicio,
        end_data_hora=fim,
    )

def test_mad_zero_valor_igual_mediana_retorna_zero():

    baseline = criar_baseline_teste(
    parametro=ParametroVital.TEMPERATURA,
    mediana=37.5,
    mad=0.0,
)

    resultado = calculate_robust_zscore(
        valor_atual_valor=37.5,
        baseline=baseline,
    )

    assert resultado.computable is True
    assert resultado.robust_zscore == 0.0

def test_mad_zero_valor_diferente_nao_calcula():

    baseline = criar_baseline_teste(
    parametro=ParametroVital.TEMPERATURA,
    mediana=37.5,
    mad=0.0,
)

    resultado = calculate_robust_zscore(
        valor_atual_valor=38.0,
        baseline=baseline,
    )

    assert resultado.computable is False
    assert resultado.robust_zscore is None

import pytest


def test_mad_maior_zero_calcula_z():

    baseline = criar_baseline_teste(
        parametro=ParametroVital.SPO2,
        mediana=98.0,
        mad=0.1,
    )

    resultado = calculate_robust_zscore(
        valor_atual_valor=97.0,
        baseline=baseline,
    )

    assert resultado.computable is True

    assert resultado.robust_zscore is not None

    assert resultado.robust_zscore == pytest.approx(
        -6.7449,
        rel=1e-3,
    )