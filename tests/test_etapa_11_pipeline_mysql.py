from datetime import datetime

from src.infrastructure.database import get_db_connection

from src.domain.alert import TipoEventoAlerta
from src.domain.measurement import ParametroVital

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

from src.ia.rules.motor_regras import (
    ConfiguracaoRegra,
    MotorRegraParametro,
)

from src.infrastructure.repositories.repositorio_alertas import (
    RepositorioAlertas,
)

from src.infrastructure.repositories.repositorio_medicoes import (
    RepositorioMedicoes,
)

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)

from src.infrastructure.simulation.cenarios import (
    CenarioSimulacao,
    ConfiguracaoCenario,
    aplicar_cenario,
)

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)

def test_pipeline_completa_salva_alerta_mysql():

    # -----------------------------------
    # 1. Busca animal real existente
    # -----------------------------------

    conexao = get_db_connection()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            responsavel_aplicacao
        FROM animais
        ORDER BY id
        LIMIT 1
        """
    )

    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    assert animal is not None

    id_animal = animal["id"]
    id_usuario = animal["responsavel_aplicacao"]

    # -----------------------------------
    # 2. Cria sessão
    # -----------------------------------

    repositorio_sessoes = RepositorioSessoes()

    id_sessao = repositorio_sessoes.iniciar_sessao(
        animal_id=id_animal,
        usuario_id=id_usuario,
        data_hora_inicio=datetime(
            2026,
            10,
            16,
            10,
            0,
            0,
        ),
    )

    # -----------------------------------
    # 3. Gera simulação
    # -----------------------------------

    simulador = SimuladorSinaisVitais(
        id_paciente=str(id_animal),
        id_sessao=id_sessao,
        seed=42,
    )

    medicoes = simulador.generate_series(
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

    # -----------------------------------
    # 4. Aplica queda progressiva
    # -----------------------------------

    medicoes = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao
                .QUEDA_PROGRESSIVA_SPO2
            ),
            inicio_evento_segundos=300,
            queda_spo2_por_minuto=1.0,
        ),
    )

    # -----------------------------------
    # 5. Salva medições no MySQL
    # -----------------------------------

    repositorio_medicoes = (
        RepositorioMedicoes()
    )

    repositorio_medicoes.salvar_lote(
        medicoes
    )

    # -----------------------------------
    # 6. Seleciona somente SpO2
    # -----------------------------------

    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    # -----------------------------------
    # 7. Inicializa algoritmos
    # -----------------------------------

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

    repositorio_alertas = (
        RepositorioAlertas()
    )

    evento_salvo = None
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

        resultado_z = calcular_z_robusto(
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

        entrada_alerta = (
            EntradaMotorAlertas(
                id_paciente=str(id_animal),
                id_sessao=id_sessao,

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

        evento = motor_alertas.processar(
            entrada_alerta
        )

        if (
            evento is not None
            and evento.tipo_evento
            == TipoEventoAlerta.ABERTURA
        ):

            repositorio_alertas.salvar(
                evento
            )

            evento_salvo = evento

            break
    assert evento_salvo is not None

    conexao = get_db_connection()
    cursor = conexao.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *
        FROM eventos_alerta
        WHERE id_alerta = %s
        """,
        (
            evento_salvo.id_alerta,
        ),
    )

    registro = cursor.fetchone()

    cursor.close()
    conexao.close()

    assert registro is not None

    assert (
        registro["tipo_evento"]
        == "abertura"
    )

    assert (
        registro["parametro"]
        == "spo2"
    )

    assert (
        registro["sessao_id"]
        == id_sessao
    )

    print()
    print(
        "PIPELINE COMPLETA — MYSQL"
    )
    print(
        "-------------------------"
    )

    print(
        "Sessão:",
        id_sessao
    )

    print(
        "Alerta:",
        registro["id_alerta"]
    )

    print(
        "Horário:",
        registro["data_hora"]
    )

    print(
        "Valor SpO2:",
        registro["valor_atual"]
    )

    print(
        "Z robusto:",
        registro["z_robusto"]
    )

    print(
        "Motivo:",
        registro["motivo"]
    )
