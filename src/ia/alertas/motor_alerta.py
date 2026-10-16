from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from src.domain.alert import EventoAlerta,TipoEventoAlerta
from src.domain.measurement import Vitalparametro 
from src.ia.rules.motor_regras import EstadoMonitoramento

@dataclass(frozen=True)
class EntradaMotorAlertas:
    id_paciente: str
    id_sessao: str

    parametro: Vitalparametro

    data_hora: datetime

    estado: EstadoMonitoramento

    valor_atual: float

    z_robusto: float | None = None
    ewma: float | None = None
    inclinacao: float | None = None

    qualidade_sinal: float | None = None

    motivo_regra: str = ""

    dados_validos: bool = True

class MotorAlertas:

    def __init__(self):
        self._alertas_ativos: dict[tuple[str,str,Vitalparametro,],str,] = {}

    def processar(self,entrada: EntradaMotorAlertas) -> EventoAlerta | None:

        if not entrada.dados_validos:
            return None

        chave = (
            entrada.id_paciente,
            entrada.id_sessao,
            entrada.parametro,
                )

        if (entrada.estado == EstadoMonitoramento.ALERTA):

            if chave in self._alertas_ativos:
                return None

            id_alerta = str(uuid4())

            self._alertas_ativos[chave] = id_alerta

            return EventoAlerta(
                id_alerta=id_alerta,

                tipo_evento=(TipoEventoAlerta.ABERTURA),

                id_paciente=(entrada.id_paciente),

                id_sessao=(entrada.id_sessao),

                parametro=(entrada.parametro),

                data_hora=(entrada.data_hora),

                estado_monitoramento=(entrada.estado.value),

                valor_atual=(entrada.valor_atual),

                z_robusto=(entrada.z_robusto),

                ewma=entrada.ewma,

                inclinacao=(entrada.inclinacao),

                qualidade_sinal=(entrada.qualidade_sinal),

                motivo=(entrada.motivo_regra),
            )
        
        if (entrada.estado == EstadoMonitoramento.NORMAL):

            id_alerta = (self._alertas_ativos.pop(chave,None,))

            if id_alerta is None:
                return None

            return EventoAlerta(
                id_alerta=id_alerta,

                tipo_evento=(TipoEventoAlerta.ENCERRAMENTO),

                id_paciente=(entrada.id_paciente),

                id_sessao=(entrada.id_sessao),

                parametro=(entrada.parametro),

                data_hora=(entrada.data_hora),

                estado_monitoramento=(entrada.estado.value),

                valor_atual=(entrada.valor_atual),

                z_robusto=(entrada.z_robusto),

                ewma=entrada.ewma,

                inclinacao=(entrada.inclinacao),

                qualidade_sinal=(entrada.qualidade_sinal),

                motivo=(
                    "Alteração deixou de persistir "
                    "e o estado retornou ao normal."
                ),
            )

        return None

    def tem_alerta_ativo(self,id_paciente: str,id_sessao: str,parametro: Vitalparametro,) -> bool:

        chave = (id_paciente,id_sessao,parametro,)
        return chave in self._alertas_ativos
        