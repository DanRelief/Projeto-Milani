from dataclasses import dataclass
from datetime import datetime

@dataclass
class Measurement:
    tempomedicao: datetime
    fluxo_o2_ar: float       # L/min
    iso_sevo: float          # % (Agentes Inalatórios)
    etco2: float             # mmHg
    spo2: float              # % (Antigo oxigenio)
    temperatura: float       # °C
    freq_respiratoria: float # rpm
    freq_cardiaca: float     # bpm (Antigo batimento_cardiaco)
    pressao_arterial: float  # mmHg