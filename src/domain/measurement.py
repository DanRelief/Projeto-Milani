from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Vitalparametro(str, Enum):
    SPO2 = "spo2"
    TEMPERATURE = "temperature"
    MEDIA_ARTERIAL_PRESSURE = "media_arterial_pressure"


class DataSource(str, Enum):
    SIMULATOR = "simulator"
    CSV = "csv"
    MONITOR = "monitor"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"


@dataclass
class Measurement:
    id_paciente: str
    id_sessao: str

    data_hora: datetime

    parametro: Vitalparametro
    value: float
    unit: str

    source: DataSource

    qualidade_sinal: float | None = None
    valido: bool = True

    def __post_init__(self):

        if not self.id_paciente.strip():
            raise ValueError(
                "id_paciente não pode ser vazio."
            )

        if not self.id_sessao.strip():
            raise ValueError(
                "id_sessao não pode ser vazio."
            )

        if self.qualidade_sinal is not None:

            if not 0.0 <= self.qualidade_sinal <= 1.0:
                raise ValueError(
                    "qualidade_sinal deve estar entre 0.0 e 1.0."
                )