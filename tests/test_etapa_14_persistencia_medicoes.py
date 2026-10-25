from datetime import datetime

from src.application.monitoramento.controlador_monitoramento import (
    ControladorMonitoramento,
)

from src.domain.measurement import (
    FonteDados,
    Medicao,
    ParametroVital,
)


class RepositorioAlertasFake:

    def salvar(
        self,
        evento,
    ) -> None:
        pass


class RepositorioMedicoesFake:

    def __init__(self) -> None:
        self.lotes_salvos = []

    def salvar_lote(
        self,
        medicoes,
    ) -> None:

        self.lotes_salvos.append(
            list(medicoes)
        )


def test_snapshot_e_persistido():

    repositorio_medicoes = (
        RepositorioMedicoesFake()
    )

    controlador = ControladorMonitoramento(
        repositorio_alertas=(
            RepositorioAlertasFake()
        ),
        repositorio_medicoes=(
            repositorio_medicoes
        ),
    )

    controlador.iniciar_sessao(
        id_paciente="1",
        id_sessao="SESSAO_TESTE",
    )

    data_hora = datetime(
        2026,
        10,
        18,
        17,
        0,
        0,
    )

    medicoes = [
        Medicao(
            id_paciente="1",
            id_sessao="SESSAO_TESTE",
            data_hora=data_hora,
            parametro=ParametroVital.SPO2,
            valor=98.0,
            unidade="%",
            fonte=FonteDados.SIMULADOR,
            qualidade_sinal=1.0,
        ),
        Medicao(
            id_paciente="1",
            id_sessao="SESSAO_TESTE",
            data_hora=data_hora,
            parametro=(
                ParametroVital.TEMPERATURA
            ),
            valor=37.5,
            unidade="°C",
            fonte=FonteDados.SIMULADOR,
            qualidade_sinal=1.0,
        ),
        Medicao(
            id_paciente="1",
            id_sessao="SESSAO_TESTE",
            data_hora=data_hora,
            parametro=(
                ParametroVital
                .PRESSAO_ARTERIAL_MEDIA
            ),
            valor=85.0,
            unidade="mmHg",
            fonte=FonteDados.SIMULADOR,
            qualidade_sinal=1.0,
        ),
    ]

    controlador.processar_medicoes(
        medicoes
    )

    assert len(
        repositorio_medicoes.lotes_salvos
    ) == 1

    lote = (
        repositorio_medicoes
        .lotes_salvos[0]
    )

    assert len(lote) == 3

    assert (
        lote[0].parametro
        == ParametroVital.SPO2
    )

    assert (
        lote[1].parametro
        == ParametroVital.TEMPERATURA
    )

    assert (
        lote[2].parametro
        == ParametroVital
        .PRESSAO_ARTERIAL_MEDIA
    )

    print()
    print(
        "PERSISTÊNCIA DE MEDIÇÕES"
    )
    print(
        "-----------------------"
    )
    print(
        "Lotes salvos:",
        len(
            repositorio_medicoes
            .lotes_salvos
        ),
    )
    print(
        "Medições no lote:",
        len(lote),
    )