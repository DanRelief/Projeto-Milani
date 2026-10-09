from dataclasses import dataclass
from datetime import datetime


@dataclass
class Measurement:
    tempomedicao: datetime
    oxigenio: float
    batimento_cardiaco: float
    pressao_arterial: float
  