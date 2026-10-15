from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class VitalParameter(str, Enum):
    SPO2 = "spo2"
    TEMPERATURE = "temperature"
    MEAN_ARTERIAL_PRESSURE = "mean_arterial_pressure"


class DataSource(str, Enum):
    SIMULATOR = "simulator"
    CSV = "csv"
    MONITOR = "monitor"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"


@dataclass
class Measurement:
    patient_id: str
    session_id: str

    timestamp: datetime

    parameter: VitalParameter
    value: float
    unit: str

    source: DataSource

    signal_quality: float | None = None
    is_valid: bool = True

    def __post_init__(self):

        if not self.patient_id.strip():
            raise ValueError(
                "patient_id não pode ser vazio."
            )

        if not self.session_id.strip():
            raise ValueError(
                "session_id não pode ser vazio."
            )

        if self.signal_quality is not None:

            if not 0.0 <= self.signal_quality <= 1.0:
                raise ValueError(
                    "signal_quality deve estar entre 0.0 e 1.0."
                )