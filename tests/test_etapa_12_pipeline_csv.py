from pathlib import Path
from datetime import datetime

from src.domain.alert import TipoEventoAlerta
from src.domain.measurement import ParametroVital
from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    DirecaoAlteracao,
)
from src.application.buffering.vital_buffer import VitalBuffer
from src.ia.alertas.motor_alerta import (
    EntradaMotorAlertas,
    MotorAlertas,
)

from src.ia.baseline.rolling import (
    calculate_rolling_baseline,
)

from src.ia.baseline.robust_zscore import (
    calculate_robust_zscore,
)

from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    MotorRegraParametro,
)

from src.infrastructure.ingestion.leitor_csv import (
    LeitorCSV,
)
from datetime import datetime


INICIO_DETERIORACAO = datetime(
    2026,
    10,
    17,
    10,
    7,
    0,
)

INICIO_PARADA = datetime(
    2026,
    10,
    17,
    10,
    12,
    0,
)

INICIO_RECUPERACAO = datetime(
    2026,
    10,
    17,
    10,
    15,
    0,
)

PASTA_DADOS = (
    Path(__file__).parent
    / "dados"
)

def processar_spo2(
    medicoes,
):

    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    medicoes_spo2.sort(
        key=lambda medicao: medicao.data_hora
    )

    if not medicoes_spo2:
        return []

    primeira_medicao = medicoes_spo2[0]

    buffer_vitais = VitalBuffer(
        id_paciente=primeira_medicao.id_paciente,
        id_sessao=primeira_medicao.id_sessao,
        max_minutes=30,
    )

    motor_regras = MotorRegraParametro(
        ConfiguracaoRegra(
            limiar_entrada_z=3.0,
            limiar_saida_z=1.5,
            janelas_persistencia=3,
            janelas_recuperacao=2,
            qualidade_minima=0.8,
            direcao=DirecaoAlteracao.QUEDA,
        )
    )

    motor_alertas = MotorAlertas()

    eventos = []

    for medicao_atual in medicoes_spo2:

        buffer_vitais.add(
            medicao_atual
        )

        janela = buffer_vitais.get_recent(
            parametro=ParametroVital.SPO2,
            minutes=5,
        )

        if len(janela) < 6:
            continue

        try:

            baseline = calculate_rolling_baseline(
                janela,
                exclude_valor_atual=True,
                minimo_samples=5,
            )

        except ValueError:
            continue

        resultado_z = calculate_robust_zscore(
            valor_atual_valor=(
                medicao_atual.valor
            ),
            baseline=baseline,
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

        entrada_alerta = EntradaMotorAlertas(
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

        evento = motor_alertas.processar(
            entrada_alerta
        )

        if evento is not None:
            eventos.append(
                evento
            )

    return eventos


def test_csv_estavel_nao_deve_gerar_alerta():

    leitor = LeitorCSV()

    caminho = (
        PASTA_DADOS
        / "sinais_vitais_simulados_15min.csv"
    )

    medicoes = leitor.ler(
        caminho_arquivo=caminho,
        id_paciente="1",
        id_sessao="CSV_ESTAVEL",
    )

    eventos = processar_spo2(
        medicoes
    )

    aberturas = [
        evento
        for evento in eventos
        if evento.tipo_evento
        == TipoEventoAlerta.ABERTURA
    ]

    print()
    print("CSV ESTÁVEL — PIPELINE")
    print("----------------------")

    print(
        "Medições:",
        len(medicoes)
    )

    print(
        "Alertas abertos:",
        len(aberturas)
    )

    assert len(aberturas) == 0


def test_csv_evento_deve_gerar_alerta():

    leitor = LeitorCSV()

    caminho = (
        PASTA_DADOS
        / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
    )

    medicoes = leitor.ler(
        caminho_arquivo=caminho,
        id_paciente="1",
        id_sessao="CSV_EVENTO",
    )

    eventos = processar_spo2(
        medicoes
    )

    aberturas = [
        evento
        for evento in eventos
        if evento.tipo_evento
        == TipoEventoAlerta.ABERTURA
    ]

    print()
    print("CSV EVENTO — PIPELINE")
    print("---------------------")

    print(
        "Medições:",
        len(medicoes)
    )

    print(
        "Alertas abertos:",
        len(aberturas)
    )

    for evento in aberturas:

        print()
        print(
            "Horário:",
            evento.data_hora
        )

        print(
            "SpO2:",
            evento.valor_atual
        )

        print(
            "Z robusto:",
            evento.z_robusto
        )

        print(
            "Motivo:",
            evento.motivo
        )

    assert len(aberturas) >= 1

def test_csv_parada_tem_spo2_indisponivel():

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_EVENTO",
    )

    medicoes_spo2_parada = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.SPO2
            and
            INICIO_PARADA
            <= medicao.data_hora
            < INICIO_RECUPERACAO
        )
    ]

    assert (
        len(medicoes_spo2_parada)
        == 0
    )

def test_csv_parada_tem_pam_zero():

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_EVENTO",
    )

    medicoes_pam_parada = [
        medicao
        for medicao in medicoes
        if (
            medicao.parametro
            == ParametroVital.PRESSAO_ARTERIAL_MEDIA
            and
            INICIO_PARADA
            <= medicao.data_hora
            < INICIO_RECUPERACAO
        )
    ]

    assert len(
        medicoes_pam_parada
    ) > 0

    assert all(
        medicao.valor == 0.0
        for medicao in medicoes_pam_parada
    )