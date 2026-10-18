from datetime import datetime, timedelta

from src.application.monitoramento.controlador_monitoramento import (
    ControladorMonitoramento,
)

from src.domain.alert import (
    TipoEventoAlerta,
)

from src.domain.measurement import (
    FonteDados,
    Medicao,
    ParametroVital,
)


ID_PACIENTE = "DOG_TESTE_001"
ID_SESSAO = "SESSAO_TESTE_001"

INICIO = datetime(
    2026,
    10,
    18,
    15,
    0,
    0,
)


class RepositorioAlertasFake:
    """
    Substitui o MySQL durante o teste.

    Tudo que o controlador tentar salvar
    fica armazenado em memória.
    """

    def __init__(self) -> None:
        self.eventos_salvos = []

    def salvar(
        self,
        evento,
    ) -> None:
        self.eventos_salvos.append(
            evento
        )


def criar_medicao(
    parametro: ParametroVital,
    valor: float,
    unidade: str,
    data_hora: datetime,
) -> Medicao:

    return Medicao(
        id_paciente=ID_PACIENTE,
        id_sessao=ID_SESSAO,
        data_hora=data_hora,
        parametro=parametro,
        valor=valor,
        unidade=unidade,
        fonte=FonteDados.SIMULADOR,
        qualidade_sinal=1.0,
    )


def criar_snapshot(
    data_hora: datetime,
    spo2: float,
    temperatura: float,
    pam: float,
) -> list[Medicao]:

    return [
        criar_medicao(
            parametro=ParametroVital.SPO2,
            valor=spo2,
            unidade="%",
            data_hora=data_hora,
        ),
        criar_medicao(
            parametro=ParametroVital.TEMPERATURA,
            valor=temperatura,
            unidade="°C",
            data_hora=data_hora,
        ),
        criar_medicao(
            parametro=(
                ParametroVital
                .PRESSAO_ARTERIAL_MEDIA
            ),
            valor=pam,
            unidade="mmHg",
            data_hora=data_hora,
        ),
    ]


def criar_controlador(
    repositorio_alertas,
) -> ControladorMonitoramento:

    controlador = ControladorMonitoramento(
        repositorio_alertas=(
            repositorio_alertas
        )
    )

    controlador.iniciar_sessao(
        id_paciente=ID_PACIENTE,
        id_sessao=ID_SESSAO,
    )

    return controlador


def aquecer_controlador(
    controlador: ControladorMonitoramento,
) -> datetime:

    valores_spo2 = [
        98.00,
        98.10,
        97.90,
        98.05,
        97.95,
        98.00,
        98.08,
        97.92,
    ]

    valores_temperatura = [
        37.50,
        37.52,
        37.48,
        37.51,
        37.49,
        37.50,
        37.51,
        37.49,
    ]

    valores_pam = [
        85.0,
        86.0,
        84.0,
        85.5,
        84.5,
        85.0,
        85.4,
        84.6,
    ]

    data_hora = INICIO

    for indice in range(
        len(valores_spo2)
    ):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=data_hora,
                spo2=valores_spo2[indice],
                temperatura=(
                    valores_temperatura[indice]
                ),
                pam=valores_pam[indice],
            )
        )

        data_hora += timedelta(
            seconds=5
        )

    return data_hora

def test_abertura_alerta_e_persistida():

    repositorio_falso = (
        RepositorioAlertasFake()
    )

    controlador = criar_controlador(
        repositorio_falso
    )

    data_hora = aquecer_controlador(
        controlador
    )

    # Três alterações persistentes:
    # OBSERVAÇÃO -> OBSERVAÇÃO -> ALERTA
    for indice in range(3):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    data_hora
                    + timedelta(
                        seconds=indice * 5
                    )
                ),
                spo2=95.0,
                temperatura=37.50,
                pam=85.0,
            )
        )

    assert len(
        repositorio_falso.eventos_salvos
    ) == 1

    evento = (
        repositorio_falso
        .eventos_salvos[0]
    )

    assert (
        evento.tipo_evento
        == TipoEventoAlerta.ABERTURA
    )

    assert (
        evento.parametro
        == ParametroVital.SPO2
    )

    assert (
        evento.id_sessao
        == ID_SESSAO
    )

    print()
    print(
        "PERSISTÊNCIA DE ABERTURA"
    )
    print(
        "-----------------------"
    )

    print(
        "Eventos salvos:",
        len(
            repositorio_falso
            .eventos_salvos
        ),
    )

    print(
        "Tipo:",
        evento.tipo_evento.value,
    )

    print(
        "Parâmetro:",
        evento.parametro.value,
    )

def test_abertura_e_encerramento_sao_persistidos():

    repositorio_falso = (
        RepositorioAlertasFake()
    )

    controlador = criar_controlador(
        repositorio_falso
    )

    data_hora = aquecer_controlador(
        controlador
    )

    # Abre alerta.
    for indice in range(3):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    data_hora
                    + timedelta(
                        seconds=indice * 5
                    )
                ),
                spo2=95.0,
                temperatura=37.50,
                pam=85.0,
            )
        )

    assert len(
        repositorio_falso.eventos_salvos
    ) == 1

    # Restaura o sinal.
    inicio_recuperacao = (
        data_hora
        + timedelta(seconds=15)
    )

    for indice in range(3):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    inicio_recuperacao
                    + timedelta(
                        seconds=indice * 5
                    )
                ),
                spo2=98.0,
                temperatura=37.50,
                pam=85.0,
            )
        )

    eventos = (
        repositorio_falso
        .eventos_salvos
    )

    assert len(eventos) == 2

    assert (
        eventos[0].tipo_evento
        == TipoEventoAlerta.ABERTURA
    )

    assert (
        eventos[1].tipo_evento
        == TipoEventoAlerta.ENCERRAMENTO
    )

    # Os dois eventos devem representar
    # o mesmo alerta.
    assert (
        eventos[0].id_alerta
        == eventos[1].id_alerta
    )

    print()
    print(
        "CICLO COMPLETO DO ALERTA"
    )
    print(
        "------------------------"
    )

    for evento in eventos:

        print(
            evento.tipo_evento.value,
            "->",
            evento.parametro.value,
            "| alerta:",
            evento.id_alerta,
        )

class RepositorioAlertasComErro:

    def salvar(
        self,
        evento,
    ) -> None:

        raise RuntimeError(
            "Banco indisponível para teste"
        )
    
def test_falha_persistencia_nao_interrompe_monitoramento():

    repositorio_com_erro = (
        RepositorioAlertasComErro()
    )

    controlador = criar_controlador(
        repositorio_com_erro
    )

    data_hora = aquecer_controlador(
        controlador
    )

    # Isso deverá gerar um evento,
    # o repository falhará,
    # mas processar_medicoes não deverá
    # propagar a exceção.
    for indice in range(3):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    data_hora
                    + timedelta(
                        seconds=indice * 5
                    )
                ),
                spo2=95.0,
                temperatura=37.50,
                pam=85.0,
            )
        )

    analise_spo2 = (
        controlador.analises_atuais[
            ParametroVital.SPO2
        ]
    )

    assert (
        analise_spo2["status"]
        == "alerta"
    )

    print()
    print(
        "FALHA DE PERSISTÊNCIA"
    )
    print(
        "---------------------"
    )
    print(
        "Monitoramento continuou:"
        " SIM"
    )