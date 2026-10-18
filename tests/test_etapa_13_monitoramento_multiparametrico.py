from datetime import datetime, timedelta

from ia.baseline.robust_zscore import calculate_robust_zscore
from ia.baseline.rolling import BaselineStats
from src.application.monitoramento.controlador_monitoramento import (
    ControladorMonitoramento,
)

from src.domain.measurement import (
    FonteDados,
    Medicao,
    ParametroVital,
)
from src.domain.alert import (
    TipoEventoAlerta,
)


ID_PACIENTE = "DOG_TESTE_001"
ID_SESSAO = "SESSAO_TESTE_001"

INICIO = datetime(
    2026,
    10,
    18,
    10,
    0,
    0,
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


def criar_controlador() -> ControladorMonitoramento:

    controlador = ControladorMonitoramento()

    controlador.iniciar_sessao(
        id_paciente=ID_PACIENTE,
        id_sessao=ID_SESSAO,
    )

    return controlador


def aquecer_controlador(
    controlador: ControladorMonitoramento,
) -> datetime:
    """
    Envia sinais estáveis com pequenas variações.

    As variações evitam MAD = 0 e permitem
    calcular o Robust Z normalmente.
    """

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

        snapshot = criar_snapshot(
            data_hora=data_hora,
            spo2=valores_spo2[indice],
            temperatura=(
                valores_temperatura[indice]
            ),
            pam=valores_pam[indice],
        )

        controlador.processar_medicoes(
            snapshot
        )

        data_hora += timedelta(
            seconds=5
        )

    return data_hora

def test_tres_parametros_estaveis_ficam_normais():

    controlador = criar_controlador()

    aquecer_controlador(
        controlador
    )

    analises = (
        controlador.analises_atuais
    )

    assert (
        analises[
            ParametroVital.SPO2
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital.TEMPERATURA
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "normal"
    )

    print()
    print(
        "MONITORAMENTO MULTIPARAMÉTRICO"
    )
    print(
        "-----------------------------"
    )

    print(
        "SpO2:",
        analises[
            ParametroVital.SPO2
        ]["status"],
    )

    print(
        "Temperatura:",
        analises[
            ParametroVital.TEMPERATURA
        ]["status"],
    )

    print(
        "PAM:",
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"],
    )

def test_queda_pam_nao_altera_estado_dos_outros_parametros():

    controlador = criar_controlador()

    data_hora = aquecer_controlador(
        controlador
    )

    # Primeira medição alterada:
    # deve iniciar observação.
    controlador.processar_medicoes(
        criar_snapshot(
            data_hora=data_hora,
            spo2=98.0,
            temperatura=37.50,
            pam=70.0,
        )
    )

    analises = (
        controlador.analises_atuais
    )

    assert (
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "observacao"
    )

    assert (
        analises[
            ParametroVital.SPO2
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital.TEMPERATURA
        ]["status"]
        == "normal"
    )

    # Mais duas medições persistentes.
    for deslocamento in (
        5,
        10,
    ):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    data_hora
                    + timedelta(
                        seconds=deslocamento
                    )
                ),
                spo2=98.0,
                temperatura=37.50,
                pam=70.0,
            )
        )

    analises = (
        controlador.analises_atuais
    )

    print()
    print(
        "QUEDA ISOLADA DE PAM"
    )
    print(
        "--------------------"
    )

    print(
        "SpO2:",
        analises[
            ParametroVital.SPO2
        ]["status"],
    )

    print(
        "Temperatura:",
        analises[
            ParametroVital.TEMPERATURA
        ]["status"],
    )

    print(
        "PAM:",
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"],
    )

    assert (
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "alerta"
    )

    assert (
        analises[
            ParametroVital.SPO2
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital.TEMPERATURA
        ]["status"]
        == "normal"
    )


def test_spo2_e_pam_podem_ficar_em_alerta_simultaneamente():

    controlador = criar_controlador()

    eventos = []

    controlador.evento_alerta_gerado.connect(
        eventos.append
    )

    data_hora = aquecer_controlador(
        controlador
    )

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
                pam=70.0,
            )
        )

    analises = (
        controlador.analises_atuais
    )

    print()
    print(
        "ALERTA MULTIPARAMÉTRICO"
    )
    print(
        "----------------------"
    )

    for parametro in (
        ParametroVital.SPO2,
        ParametroVital.TEMPERATURA,
        ParametroVital.PRESSAO_ARTERIAL_MEDIA,
    ):

        analise = analises[
            parametro
        ]

        print(
            analise["nome"],
            "->",
            analise["status"],
            "| Z =",
            analise["z_robusto"],
        )

    print()
    print(
        "Eventos gerados:",
        len(eventos)
    )

    assert (
        analises[
            ParametroVital.SPO2
        ]["status"]
        == "alerta"
    )

    assert (
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "alerta"
    )

    assert (
        analises[
            ParametroVital.TEMPERATURA
        ]["status"]
        == "normal"
    )

    parametros_com_evento = {
        evento.parametro
        for evento in eventos
    }

    assert (
        ParametroVital.SPO2
        in parametros_com_evento
    )

    assert (
        ParametroVital
        .PRESSAO_ARTERIAL_MEDIA
        in parametros_com_evento
    )

def test_alertas_recuperam_e_sao_encerrados():

    controlador = criar_controlador()

    eventos = []

    controlador.evento_alerta_gerado.connect(
        eventos.append
    )

    data_hora = aquecer_controlador(
        controlador
    )

    # Provoca alerta simultâneo em SpO₂ e PAM.
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
                pam=70.0,
            )
        )

    assert (
        controlador.analises_atuais[
            ParametroVital.SPO2
        ]["status"]
        == "alerta"
    )

    assert (
        controlador.analises_atuais[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "alerta"
    )

    # Restaura os sinais.
    data_recuperacao = (
        data_hora
        + timedelta(seconds=15)
    )

    for indice in range(3):

        controlador.processar_medicoes(
            criar_snapshot(
                data_hora=(
                    data_recuperacao
                    + timedelta(
                        seconds=indice * 5
                    )
                ),
                spo2=98.0,
                temperatura=37.50,
                pam=85.0,
            )
        )

    analises = (
        controlador.analises_atuais
    )
    eventos_encerramento = [
        evento
        for evento in eventos
        if evento.tipo_evento
        == TipoEventoAlerta.ENCERRAMENTO
    ]
    
    parametros_encerrados = {
        evento.parametro
        for evento in eventos_encerramento
    }

    assert (
        ParametroVital.SPO2
        in parametros_encerrados
    )

    assert (
        ParametroVital.PRESSAO_ARTERIAL_MEDIA
        in parametros_encerrados
    )

    print()
    print(
        "RECUPERAÇÃO MULTIPARAMÉTRICA"
    )
    print(
        "---------------------------"
    )

    print(
        "SpO2:",
        analises[
            ParametroVital.SPO2
        ]["status"],
    )

    print(
        "Temperatura:",
        analises[
            ParametroVital.TEMPERATURA
        ]["status"],
    )

    print(
        "PAM:",
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"],
    )

    print(
        "Eventos totais:",
        len(eventos)
    )

    assert (
        analises[
            ParametroVital.SPO2
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital
            .PRESSAO_ARTERIAL_MEDIA
        ]["status"]
        == "normal"
    )

    assert (
        analises[
            ParametroVital.TEMPERATURA
        ]["status"]
        == "normal"
    )
