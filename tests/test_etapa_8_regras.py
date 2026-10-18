from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    EstadoMonitoramento,
    MotorRegraParametro,
)
from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    DirecaoAlteracao,
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

def test_regra_queda_ignora_z_positivo():

    motor = MotorRegraParametro(
        ConfiguracaoRegra(
            direcao=DirecaoAlteracao.QUEDA,
        )
    )

    resultado = motor.processar(
        z_robusto=4.0,
        qualidade_sinal=1.0,
    )

    assert (
        resultado.alteracao_detectada
        is False
    )

def test_regra_queda_detecta_z_negativo():

    motor = MotorRegraParametro(
        ConfiguracaoRegra(
            direcao=DirecaoAlteracao.QUEDA,
        )
    )

    resultado = motor.processar(
        z_robusto=-4.0,
        qualidade_sinal=1.0,
    )

    assert (
        resultado.alteracao_detectada
        is True
    )

def test_regra_ambas_detecta_as_duas_direcoes():

    configuracao = ConfiguracaoRegra(
        direcao=DirecaoAlteracao.AMBAS,
    )

    motor_positivo = MotorRegraParametro(
        configuracao
    )

    resultado_positivo = (
        motor_positivo.processar(
            z_robusto=4.0,
            qualidade_sinal=1.0,
        )
    )

    motor_negativo = MotorRegraParametro(
        configuracao
    )

    resultado_negativo = (
        motor_negativo.processar(
            z_robusto=-4.0,
            qualidade_sinal=1.0,
        )
    )

    assert (
        resultado_positivo
        .alteracao_detectada
        is True
    )

    assert (
        resultado_negativo
        .alteracao_detectada
        is True
    )