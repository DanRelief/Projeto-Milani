from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ParametroVital(str, Enum):
    OXIGENIO = "oxigenio"
    PRESSAO_ARTERIAL = "pressao_arterial"
    TEMPERATURA = "temperatura"


@dataclass
class Measurement:
    tempomedicao: datetime
    oxigenio: float          # SpO2 (%)
    pressao_arterial: float  # (mmHg)
    temperatura: float       # (°C)