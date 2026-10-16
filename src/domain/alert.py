from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.domain.measurement import Vitalparametro



class TipoEventoAlerta(str, Enum):
    ABERTURA = "abertura"
    ENCERRAMENTO = "encerramento"


@dataclass(frozen=True)
class EventoAlerta:
    id_alerta: str

    tipo_evento: TipoEventoAlerta

    id_paciente: str
    id_sessao: str

    parametro: Vitalparametro

    data_hora: datetime

    estado_monitoramento: str

    valor_atual: float

    z_robusto: float | None = None
    ewma: float | None = None
    inclinacao: float | None = None

    qualidade_sinal: float | None = None

    motivo: str = ""