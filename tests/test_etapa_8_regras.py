from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    EstadoMonitoramento,
    MotorRegraParametro,
)


def test_persistencia_e_histerese():

    configuracao = ConfiguracaoRegra(
        limiar_entrada_z=3.0,
        limiar_saida_z=1.5,
        janelas_persistencia=3,
        janelas_recuperacao=2,
        qualidade_minima=0.8,
    )

    motor = MotorRegraParametro(
        configuracao=configuracao
    )

    # Estado inicial
    resultado = motor.processar(
        z_robusto=0.5,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.NORMAL
    )

    # Primeira alteração
    resultado = motor.processar(
        z_robusto=3.2,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.OBSERVACAO
    )

    # Segunda alteração consecutiva
    resultado = motor.processar(
        z_robusto=3.5,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.OBSERVACAO
    )

    # Terceira alteração consecutiva
    resultado = motor.processar(
        z_robusto=4.0,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.ALERTA
    )

    # Ainda não recuperou
    resultado = motor.processar(
        z_robusto=2.0,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.ALERTA
    )

    # Primeira janela recuperada
    resultado = motor.processar(
        z_robusto=1.2,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.RECUPERACAO
    )

    # Segunda janela recuperada
    resultado = motor.processar(
        z_robusto=0.8,
        qualidade_sinal=0.95,
    )

    assert (
        resultado.estado
        == EstadoMonitoramento.NORMAL
    )

def test_qualidade_sinal_baixa():

    motor = MotorRegraParametro()

    resultado = motor.processar(
        z_robusto=10.0,
        qualidade_sinal=0.2,
    )

    assert resultado.dados_validos is False

    assert (
        resultado.estado
        == EstadoMonitoramento.NORMAL
    )