from datetime import datetime, timedelta

from src.domain.measurement import (
    FonteDados,
    Medicao,
    Vitalparametro,
)

from src.ia.features.feature_extractor import (
    FeatureExtractor,
)


def test_features_spo2():

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
        97.0,
        96.0,
        95.0,
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
                    + timedelta(minutes=index)
                ),

                parametro=Vitalparametro.SPO2,
                value=value,
                unit="%",

                source=FonteDados.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    extractor = FeatureExtractor()

    features = extractor.extract(
        measurements,
        window_minutes=5,
    )

    print()
    print("Features SpO2")
    print("----------------")

    print("valor_atual:", features.valor_atual)
    print("media:", features.media)
    print("mediana:", features.mediana)
    print("Min:", features.minimo)
    print("Max:", features.maximo)
    print("desvio_padrao:", features.desvio_padrao)
    print("Delta:", features.delta)
    print("inclinacao:", features.inclinacao)

    assert features.valor_atual == 94.0

    assert features.media == 96.0

    assert features.mediana == 96.0

    assert features.minimo == 94.0

    assert features.maximo == 98.0

    assert features.delta == -4.0

    assert round(
        features.inclinacao,
        2
    ) == -1.0


from src.application.buffering.vital_buffer import VitalBuffer

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)


def test_features_com_simulador():

    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_001",
        id_sessao="SESSION_001",
        seed=42,
    )

    buffer = VitalBuffer(
        id_paciente="DOG_001",
        id_sessao="SESSION_001",
        max_minutes=30,
    )

    measurements = simulador.generate_series(
        duration_minutes=10,
        interval_seconds=5,
        start_time=datetime(
            2026,
            10,
            15,
            10,
            0,
            0,
        ),
    )

    buffer.add_many(
        measurements
    )

    extractor = FeatureExtractor()

    for parametro in [
        Vitalparametro.SPO2,
        Vitalparametro.TEMPERATURE,
        Vitalparametro.media_ARTERIAL_PRESSURE,
    ]:

        window = buffer.get_recent(
            parametro,
            minutes=5,
        )

        features = extractor.extract(
            window,
            window_minutes=5,
        )

        print()
        print(
            "Parâmetro:",
            parametro.value
        )

        print(
            "Quantidade:",
            features.count
        )

        print(
            "Atual:",
            round(
                features.valor_atual,
                3
            )
        )

        print(
            "Média:",
            round(
                features.media,
                3
            )
        )

        print(
            "medianaa:",
            round(
                features.mediana,
                3
            )
        )

        print(
            "desvio_padrao:",
            round(
                features.desvio_padrao,
                3
            )
        )

        print(
            "Delta:",
            round(
                features.delta,
                3
            )
        )

        print(
            "inclinacao:",
            round(
                features.inclinacao,
                3
            )
        )

        assert features.count > 0

def test_inclinacao_constante():

    start = datetime(
        2026,
        10,
        15,
        10,
        0,
        0,
    )

    measurements = []

    for index in range(5):
        measurements.append(
            Medicao(
                id_paciente="DOG_001",
                id_sessao="SESSION_001",
                data_hora=start
                + timedelta(minutes=index),
                parametro=Vitalparametro.SPO2,
                value=98.0,
                unit="%",
                source=FonteDados.SIMULATOR,
                qualidade_sinal=1.0,
            )
        )

    extractor = FeatureExtractor()

    features = extractor.extract(
        measurements,
        window_minutes=5,
    )

    assert features.delta == 0.0
    assert features.inclinacao == 0.0
    assert features.desvio_padrao == 0.0