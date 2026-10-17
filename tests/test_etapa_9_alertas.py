from datetime import (
    datetime,
    timedelta,
)

from src.ia.alertas.motor_alerta import (
    EntradaMotorAlertas,
    MotorAlertas,
)

from src.domain.alert import (
    TipoEventoAlerta,
)

from src.domain.measurement import (
    ParametroVital,
)

from src.ia.rules.motor_regras import (
    EstadoMonitoramento,
)


def criar_entrada(
    estado: EstadoMonitoramento,
    segundos: int,
    z_robusto: float,
    dados_validos: bool = True,
):

    return EntradaMotorAlertas(
        id_paciente="DOG_001",
        id_sessao="SESSION_001",

        parametro=ParametroVital.SPO2,

        data_hora=(
            datetime(
                2026,
                10,
                16,
                10,
                0,
                0,
            )
            + timedelta(
                seconds=segundos
            )
        ),

        estado=estado,

        valor_atual=94.0,

        z_robusto=z_robusto,

        ewma=96.0,

        inclinacao=-0.8,

        qualidade_sinal=0.95,

        motivo_regra=(
            "Alteração persistente detectada."
        ),

        dados_validos=dados_validos,
    )

def test_abertura_e_encerramento_alerta():

    motor = MotorAlertas()

    entrada_normal = criar_entrada(
        EstadoMonitoramento.NORMAL,
        segundos=0,
        z_robusto=0.5,
    )

    evento = motor.processar(
        entrada_normal
    )

    assert evento is None


    entrada_alerta = criar_entrada(
        EstadoMonitoramento.ALERTA,
        segundos=5,
        z_robusto=-4.2,
    )

    evento_abertura = motor.processar(
        entrada_alerta
    )

    assert evento_abertura is not None

    assert (
        evento_abertura.tipo_evento
        == TipoEventoAlerta.ABERTURA
    )

    assert motor.tem_alerta_ativo(
        "DOG_001",
        "SESSION_001",
        ParametroVital.SPO2,
    )


    # Continua em alerta.
    # NÃO queremos outro alerta.
    evento_repetido = motor.processar(
        criar_entrada(
            EstadoMonitoramento.ALERTA,
            segundos=10,
            z_robusto=-5.0,
        )
    )

    assert evento_repetido is None


    # Entrou em recuperação.
    # Ainda não encerra.
    evento_recuperacao = motor.processar(
        criar_entrada(
            EstadoMonitoramento.RECUPERACAO,
            segundos=15,
            z_robusto=-1.2,
        )
    )

    assert evento_recuperacao is None


    # Voltou para normal.
    evento_encerramento = motor.processar(
        criar_entrada(
            EstadoMonitoramento.NORMAL,
            segundos=20,
            z_robusto=-0.5,
        )
    )

    assert evento_encerramento is not None

    assert (
        evento_encerramento.tipo_evento
        == TipoEventoAlerta.ENCERRAMENTO
    )

    assert (
        evento_encerramento.id_alerta
        == evento_abertura.id_alerta
    )

    assert not motor.tem_alerta_ativo(
        "DOG_001",
        "SESSION_001",
        ParametroVital.SPO2,
    )

def test_nao_abre_alerta_com_dados_invalidos():

    motor = MotorAlertas()

    entrada = criar_entrada(
        EstadoMonitoramento.ALERTA,
        segundos=0,
        z_robusto=-10.0,
        dados_validos=False,
    )

    evento = motor.processar(
        entrada
    )

    assert evento is None

    assert not motor.tem_alerta_ativo(
        "DOG_001",
        "SESSION_001",
        ParametroVital.SPO2,
    )