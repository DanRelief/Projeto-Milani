from datetime import datetime,timedelta
from src.domain.measurement import ParametroVital
from src.infrastructure.simulation.cenarios import CenarioSimulacao,ConfiguracaoCenario,aplicar_cenario
from src.infrastructure.simulation.sinais_vitais_simulacao import SimuladorSinaisVitais
from src.ia.alertas.motor_alerta import (
    EntradaMotorAlertas,
    MotorAlertas,
)

from src.ia.baseline.rolling import (
    calculate_rolling_baseline as calcular_baseline_rolante,
)

from src.ia.baseline.robust_zscore import (
    calculate_robust_zscore as calcular_z_robusto,
)

from src.domain.alert import (
    TipoEventoAlerta,
)

from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    MotorRegraParametro,
)
def gerar_medicoes_base():

    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_001",
        id_sessao="SESSION_001",
        seed=42,
    )

    return simulador.generate_series(
        duration_minutes=10,
        interval_seconds=5,

        start_time=datetime(
            2026,
            10,
            16,
            10,
            0,
            0,
        ),
    )

def test_cenario_estavel_nao_altera_medicoes():

    medicoes = gerar_medicoes_base()

    resultado = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao.ESTAVEL
            )
        ),
    )

    valores_originais = [
        medicao.valor
        for medicao in medicoes
    ]

    valores_resultado = [
        medicao.valor
        for medicao in resultado
    ]

    assert (
        valores_originais
        == valores_resultado
    )

def test_queda_progressiva_spo2():

    medicoes = gerar_medicoes_base()

    resultado = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao.QUEDA_PROGRESSIVA_SPO2
            ),

            inicio_evento_segundos=300,

            queda_spo2_por_minuto=1.0,
        ),
    )

    spo2_original = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.SPO2
        )
    ]

    spo2_cenario = [
        medicao
        for medicao in resultado
        if (
            medicao.parametro
            == ParametroVital.SPO2
        )
    ]

    print()
    print("SpO2 original:")
    print(
        spo2_original[-1].valor
    )

    print("SpO2 com queda:")
    print(
        spo2_cenario[-1].valor
    )

    assert (
        spo2_cenario[-1].valor
        < spo2_original[-1].valor - 4.0
    )

def test_queda_progressiva_pressao():

    medicoes = gerar_medicoes_base()

    resultado = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao.QUEDA_PROGRESSIVA_PRESSAO
            ),

            inicio_evento_segundos=300,

            queda_pressao_por_minuto=4.0,
        ),
    )

    pressao_original = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.PRESSAO_ARTERIAL_MEDIA
        )
    ]

    pressao_cenario = [
        medicao
        for medicao in resultado
        if (
            medicao.parametro
            == ParametroVital.PRESSAO_ARTERIAL_MEDIA
        )
    ]

    print()
    print(
        "Pressão original:",
        pressao_original[-1].valor
    )

    print(
        "Pressão com queda:",
        pressao_cenario[-1].valor
    )

    assert (
        pressao_cenario[-1].valor
        < pressao_original[-1].valor - 15.0
    )

def test_aumento_progressivo_temperatura():

    medicoes = gerar_medicoes_base()

    resultado = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao.AUMENTO_PROGRESSIVO_TEMPERATURA
            ),

            inicio_evento_segundos=300,

            aumento_temperatura_por_minuto=0.3,
        ),
    )

    temperatura_original = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.TEMPERATURA
        )
    ]

    temperatura_cenario = [
        medicao
        for medicao in resultado
        if (
            medicao.parametro
            == ParametroVital.TEMPERATURA
        )
    ]

    print()
    print(
        "Temperatura original:",
        temperatura_original[-1].valor
    )

    print(
        "Temperatura com aumento:",
        temperatura_cenario[-1].valor
    )

    assert (
        temperatura_cenario[-1].valor
        > temperatura_original[-1].valor + 1.0
    )

#TESTE COMPLETO DE TUDO ATÉ ESTAPA 9.5
def test_queda_spo2_gera_alerta():

    medicoes = gerar_medicoes_base()

    medicoes = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao.QUEDA_PROGRESSIVA_SPO2
            ),

            inicio_evento_segundos=300,

            queda_spo2_por_minuto=1.0,
        ),
    )

    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.SPO2
        )
    ]

    motor_regras = MotorRegraParametro(
        ConfiguracaoRegra(
            limiar_entrada_z=3.0,
            limiar_saida_z=1.5,

            janelas_persistencia=3,
            janelas_recuperacao=2,

            qualidade_minima=0.8,
        )
    )

    motor_alertas = MotorAlertas()

    evento_abertura = None

    inicio_evento = (
        medicoes_spo2[0].data_hora
        + timedelta(
            seconds=300
        )
    )
    for indice in range(
        10,
        len(medicoes_spo2),
    ):

        medicao_atual = (
            medicoes_spo2[indice]
        )

        inicio_janela = max(
            0,
            indice - 60,
        )

        janela = medicoes_spo2[
            inicio_janela:
            indice + 1
        ]

        try:

            baseline = (
                calcular_baseline_rolante(
                    janela,
                    exclude_valor_atual=True,
                    minimo_samples=5,
                )
            )

        except ValueError:
            continue

        resultado_z = (
            calcular_z_robusto(
                valor_atual_valor=(
                    medicao_atual.valor
                ),
                baseline=baseline,
            )
        )

        resultado_regra = (
            motor_regras.processar(
                z_robusto=(
                    resultado_z.robust_zscore
                ),

                qualidade_sinal=(
                    medicao_atual.qualidade_sinal
                ),
            )
        )

        entrada_alerta = (
            EntradaMotorAlertas(
                id_paciente=(
                    medicao_atual.id_paciente
                ),

                id_sessao=(
                    medicao_atual.id_sessao
                ),

                parametro=(
                    medicao_atual.parametro
                ),

                data_hora=(
                    medicao_atual.data_hora
                ),

                estado=(
                    resultado_regra.estado
                ),

                valor_atual=(
                    medicao_atual.valor
                ),

                z_robusto=(
                    resultado_z.robust_zscore
                ),

                qualidade_sinal=(
                    medicao_atual.qualidade_sinal
                ),

                motivo_regra=(
                    resultado_regra.motivo
                ),

                dados_validos=(
                    resultado_regra.dados_validos
                ),
            )
        )

        evento = (
            motor_alertas.processar(
                entrada_alerta
            )
        )

        if (
            evento is not None
            and evento.tipo_evento
            == TipoEventoAlerta.ABERTURA
        ):

            evento_abertura = evento

            break

    assert evento_abertura is not None

    assert (
        evento_abertura.data_hora
        >= inicio_evento
    )

    print()
    print("ALERTA DETECTADO")
    print("----------------")

    print(
        "Horário:",
        evento_abertura.data_hora
    )

    print(
        "Valor:",
        evento_abertura.valor_atual
    )

    print(
        "Z robusto:",
        evento_abertura.z_robusto
    )

    print(
        "Motivo:",
        evento_abertura.motivo
    )

    atraso_segundos = (
        evento_abertura.data_hora
        - inicio_evento
    ).total_seconds()

    print(
        "Tempo para detecção:",
        atraso_segundos,
        "segundos"
    )
