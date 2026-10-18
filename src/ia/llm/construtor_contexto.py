from datetime import datetime

from src.domain.measurement import (
    ParametroVital,
)

from src.ia.llm.modelos_relatorio import (
    AnaliseParametroRelatorio,
    ContextoRelatorio,
)


def nome_parametro(parametro: ParametroVital,) -> str:

    nomes = {
        ParametroVital.SPO2:
            "SpO₂",

        ParametroVital.TEMPERATURA:
            "Temperatura",

        ParametroVital.PRESSAO_ARTERIAL_MEDIA:
            "Pressão Arterial Média",
    }

    return nomes.get(
        parametro,
        parametro.value,
    )


def construir_contexto_relatorio(id_paciente: str,id_sessao: str,estado_geral: str,analises_atuais: dict,) -> ContextoRelatorio:

    analises_relatorio = []

    for (
        parametro,
        analise,
    ) in analises_atuais.items():

        analises_relatorio.append(
            AnaliseParametroRelatorio(
                parametro=parametro.value,
                nome=nome_parametro(
                    parametro
                ),
                valor_atual=analise[
                    "valor"
                ],
                unidade=analise[
                    "unidade"
                ],
                mediana_baseline=(
                    analise.get(
                        "mediana_baseline"
                    )
                ),
                mad_baseline=(
                    analise.get(
                        "mad_baseline"
                    )
                ),
                z_robusto=(
                    analise.get(
                        "z_robusto"
                    )
                ),
                estado=analise[
                    "status"
                ],
                qualidade_sinal=(
                    analise.get(
                        "qualidade_sinal"
                    )
                ),
                motivo=(
                    analise.get(
                        "motivo"
                    )
                ),
            )
        )

    return ContextoRelatorio(
        id_paciente=id_paciente,
        id_sessao=id_sessao,
        data_hora_geracao=(
            datetime.now()
        ),
        estado_geral=estado_geral,
        analises=analises_relatorio,
    )