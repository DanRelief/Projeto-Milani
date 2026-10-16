from datetime import datetime

from application.buffering.vital_buffer import VitalBuffer
from src.domain.measurement import Vitalparametro
from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)


def test_simulacao_e_buffer():

    id_paciente = "DOG_001"
    id_sessao = "SESSION_001"

    simulador = SimuladorSinaisVitais(
        id_paciente=id_paciente,
        id_sessao=id_sessao,
        seed=42,
    )

    buffer = VitalBuffer(
        id_paciente=id_paciente,
        id_sessao=id_sessao,
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

    buffer.add_many(measurements)

    spo2 = buffer.get_all(
        Vitalparametro.SPO2
    )

    temperature = buffer.get_all(
        Vitalparametro.TEMPERATURA
    )

    pressure = buffer.get_all(
        Vitalparametro.PRESSAO_ARTERIAL_MEDIA
    )

    print()
    print("Quantidade SpO2:", len(spo2))
    print("Quantidade Temperatura:", len(temperature))
    print("Quantidade Pressão:", len(pressure))

    print()
    print(
        "Última SpO2:",
        buffer.latest(Vitalparametro.SPO2)
    )

    print(
        "Última temperatura:",
        buffer.latest(Vitalparametro.TEMPERATURA)
    )

    print(
        "Última pressão:",
        buffer.latest(
            Vitalparametro.PRESSAO_ARTERIAL_MEDIA
        )
    )

    assert len(spo2) == 120
    assert len(temperature) == 120
    assert len(pressure) == 120
