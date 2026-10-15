from datetime import datetime

from misa_ia.buffering.vital_buffer import VitalBuffer
from misa_ia.domain.measurement import VitalParameter
from misa_ia.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)


def test_simulacao_e_buffer():

    patient_id = "DOG_001"
    session_id = "SESSION_001"

    simulador = SimuladorSinaisVitais(
        patient_id=patient_id,
        session_id=session_id,
        seed=42,
    )

    buffer = VitalBuffer(
        patient_id=patient_id,
        session_id=session_id,
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
        VitalParameter.SPO2
    )

    temperature = buffer.get_all(
        VitalParameter.TEMPERATURE
    )

    pressure = buffer.get_all(
        VitalParameter.MEAN_ARTERIAL_PRESSURE
    )

    print()
    print("Quantidade SpO2:", len(spo2))
    print("Quantidade Temperatura:", len(temperature))
    print("Quantidade Pressão:", len(pressure))

    print()
    print(
        "Última SpO2:",
        buffer.latest(VitalParameter.SPO2)
    )

    print(
        "Última temperatura:",
        buffer.latest(VitalParameter.TEMPERATURE)
    )

    print(
        "Última pressão:",
        buffer.latest(
            VitalParameter.MEAN_ARTERIAL_PRESSURE
        )
    )

    assert len(spo2) == 120
    assert len(temperature) == 120
    assert len(pressure) == 120