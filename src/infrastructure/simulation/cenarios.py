from dataclasses import (
    dataclass,
    replace,
)

from enum import Enum

from src.domain.measurement import Medicao,ParametroVital 

class CenarioSimulacao(str, Enum):

    ESTAVEL = "estavel"

    QUEDA_PROGRESSIVA_SPO2 = ("queda_progressiva_spo2")

    QUEDA_PROGRESSIVA_PRESSAO = ("queda_progressiva_pressao")

    AUMENTO_PROGRESSIVO_TEMPERATURA = ("aumento_progressivo_temperatura")

@dataclass(frozen=True)
class ConfiguracaoCenario:

    cenario: CenarioSimulacao

    inicio_evento_segundos: float = 300.0

    queda_spo2_por_minuto: float = 1.0

    queda_pressao_por_minuto: float = 4.0

    aumento_temperatura_por_minuto: float = 0.3

def aplicar_cenario(medicoes: list[Medicao],configuracao: ConfiguracaoCenario,) -> list[Medicao]:

    if not medicoes:
        return []

    if (configuracao.cenario == CenarioSimulacao.ESTAVEL):
        return list(medicoes)

    inicio_simulacao = min(medicao.data_hora for medicao in medicoes)

    medicoes_modificadas = []

    for medicao in medicoes:

        segundos_decorridos = (
            medicao.data_hora
            - inicio_simulacao
        ).total_seconds()

        if (
            segundos_decorridos
            < configuracao.inicio_evento_segundos
        ):
            medicoes_modificadas.append(
                medicao
            )

            continue

        minutos_evento = (
            segundos_decorridos
            - configuracao.inicio_evento_segundos
        ) / 60.0

        novo_valor = (
            medicao.valor
        )

        if (
            configuracao.cenario
            == CenarioSimulacao.QUEDA_PROGRESSIVA_SPO2
            and medicao.parametro
            == ParametroVital.SPO2
        ):

            novo_valor = (
                medicao.valor
                - (
                    configuracao.queda_spo2_por_minuto
                    * minutos_evento
                )
            )

        elif (
            configuracao.cenario
            == CenarioSimulacao.QUEDA_PROGRESSIVA_PRESSAO
            and medicao.parametro
            == ParametroVital.PRESSAO_ARTERIAL_MEDIA
        ):

            novo_valor = (
                medicao.valor
                - (
                    configuracao.queda_pressao_por_minuto
                    * minutos_evento
                )
            )


        elif (
            configuracao.cenario
            == CenarioSimulacao.AUMENTO_PROGRESSIVO_TEMPERATURA
            and medicao.parametro
            == ParametroVital.TEMPERATURA
        ):

            novo_valor = (
                medicao.valor
                + (
                    configuracao.aumento_temperatura_por_minuto
                    * minutos_evento
                )
            )


        if novo_valor == medicao.valor:

            medicoes_modificadas.append(
                medicao
            )

        else:

            medicoes_modificadas.append(
                replace(
                    medicao,
                    valor=round(
                        novo_valor,
                        2,
                    ),
                )
            )

    return medicoes_modificadas