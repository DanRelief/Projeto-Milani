from datetime import datetime, timedelta

from src.ia.anomaly.construtor_dataset import (
    criar_amostras_janelas,
    criar_dataset_janelas,
)

from src.ia.anomaly.isolation_forest import (
    DetectorIsolationForest,
)

from src.domain.measurement import (
    ParametroVital,
)

from src.ia.features.feature_extractor import (
    FeatureExtractor,
)

from src.infrastructure.simulation.cenarios import (
    CenarioSimulacao,
    ConfiguracaoCenario,
    aplicar_cenario,
)

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)

def gerar_spo2_estavel(
    semente: int,
):
    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_001",
        id_sessao=f"SESSION_{semente}",
        seed=semente,
    )

    medicoes = simulador.generate_series(
        duration_minutes=20,
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

    return [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]
def criar_dataset_treinamento(
    extrator,
):
    dataset = []

    for semente in range(20):

        medicoes = gerar_spo2_estavel(
            semente
        )

        vetores = criar_dataset_janelas(
            medicoes=medicoes,
            extrator_caracteristicas=extrator,
            tamanho_janela=61,
            passo=6,
        )

        dataset.extend(
            vetores
        )

    return dataset

def criar_dataset_teste_estavel(
    extrator,
):
    medicoes = gerar_spo2_estavel(
        semente=100
    )

    return criar_dataset_janelas(
        medicoes=medicoes,
        extrator_caracteristicas=extrator,
        tamanho_janela=61,
        passo=6,
    )

def criar_amostras_teste_queda(
    extrator,
):
    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_001",
        id_sessao="SESSION_QUEDA",
        seed=101,
    )

    medicoes = simulador.generate_series(
        duration_minutes=20,
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

    medicoes = aplicar_cenario(
        medicoes,
        ConfiguracaoCenario(
            cenario=(
                CenarioSimulacao
                .QUEDA_PROGRESSIVA_SPO2
            ),

            inicio_evento_segundos=600,

            queda_spo2_por_minuto=1.0,
        ),
    )

    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    inicio_evento = (
        medicoes_spo2[0].data_hora
        + timedelta(minutes=10)
    )

    amostras = criar_amostras_janelas(
        medicoes=medicoes_spo2,
        extrator_caracteristicas=extrator,
        tamanho_janela=61,
        passo=6,
    )

    return (
        amostras,
        inicio_evento,
    )

def separar_amostras_por_periodo(
    amostras,
    inicio_evento,
):
    amostras_antes = []
    amostras_transicao = []
    amostras_depois = []

    for amostra in amostras:

        if amostra.fim < inicio_evento:

            amostras_antes.append(
                amostra
            )

        elif amostra.inicio >= inicio_evento:

            amostras_depois.append(
                amostra
            )

        else:

            amostras_transicao.append(
                amostra
            )

    return (
        amostras_antes,
        amostras_transicao,
        amostras_depois,
    )

def contar_anomalias(
    detector,
    amostras,
):
    resultados = [
        detector.avaliar(
            amostra.vetor
        )
        for amostra in amostras
    ]

    quantidade = sum(
        resultado.anomalia
        for resultado in resultados
    )

    taxa = (
        quantidade / len(resultados)
        if resultados
        else 0.0
    )

    return quantidade, taxa

def test_isolation_forest_com_cenarios():

    extrator = FeatureExtractor()

    dataset_treinamento = (
        criar_dataset_treinamento(
            extrator
        )
    )

    print()
    print(
        "Janelas de treinamento:",
        len(dataset_treinamento)
    )

    detector = DetectorIsolationForest(
        numero_arvores=200,
        semente=42,
    )

    detector.treinar(
        dataset_treinamento
    )

    # -------------------------
    # CENÁRIO ESTÁVEL
    # -------------------------

    dataset_estavel = (
        criar_dataset_teste_estavel(
            extrator
        )
    )

    resultados_estaveis = [
        detector.avaliar(vetor)
        for vetor in dataset_estavel
    ]

    quantidade_anomalias_estavel = sum(
        resultado.anomalia
        for resultado in resultados_estaveis
    )

    taxa_estavel = (
        quantidade_anomalias_estavel
        / len(resultados_estaveis)
    )

    # -------------------------
    # CENÁRIO DE QUEDA
    # -------------------------

    (
        amostras,
        inicio_evento,
    ) = criar_amostras_teste_queda(
        extrator
    )

    resultados_queda = [
        detector.avaliar(
            amostra.vetor
        )
        for amostra in amostras
    ]

    quantidade_anomalias_queda = sum(
        resultado.anomalia
        for resultado in resultados_queda
    )

    taxa_queda = (
        quantidade_anomalias_queda
        / len(resultados_queda)
    )

    print()
    print(
        "ISOLATION FOREST — CENÁRIOS"
    )
    print(
        "----------------------------"
    )

    print(
        "Estável:",
        quantidade_anomalias_estavel,
        "/",
        len(resultados_estaveis),
        "anomalias"
    )

    print(
        "Taxa estável:",
        round(
            taxa_estavel * 100,
            2
        ),
        "%"
    )

    print()

    print(
        "Queda SpO2:",
        quantidade_anomalias_queda,
        "/",
        len(resultados_queda),
        "anomalias"
    )

    print(
        "Taxa queda:",
        round(
            taxa_queda * 100,
            2
        ),
        "%"
    )

    assert (
        taxa_queda
        >
        taxa_estavel
    )
    (
        amostras_antes,
        amostras_transicao,
        amostras_depois,
    ) = separar_amostras_por_periodo(
        amostras,
        inicio_evento,
    )

    (
        quantidade_antes,
        taxa_antes,
    ) = contar_anomalias(
        detector,
        amostras_antes,
    )

    (
        quantidade_transicao,
        taxa_transicao,
    ) = contar_anomalias(
        detector,
        amostras_transicao,
    )

    (
        quantidade_depois,
        taxa_depois,
    ) = contar_anomalias(
        detector,
        amostras_depois,
    )
    print()
    print(
        "AVALIAÇÃO TEMPORAL"
    )
    print(
        "------------------"
    )

    print(
        "Antes do evento:",
        quantidade_antes,
        "/",
        len(amostras_antes),
        "-",
        round(
            taxa_antes * 100,
            2
        ),
        "%"
    )

    print(
        "Transição:",
        quantidade_transicao,
        "/",
        len(amostras_transicao),
        "-",
        round(
            taxa_transicao * 100,
            2
        ),
        "%"
    )

    print(
        "Depois do evento:",
        quantidade_depois,
        "/",
        len(amostras_depois),
        "-",
        round(
            taxa_depois * 100,
            2
        ),
        "%"
    )
    primeira_anomalia = None

    for amostra in amostras:

        resultado = detector.avaliar(
            amostra.vetor
        )

        if (
            resultado.anomalia
            and amostra.fim
            >= inicio_evento
        ):
            primeira_anomalia = (
                amostra
            )

            break
    if primeira_anomalia is not None:

        atraso = (
            primeira_anomalia.fim
            - inicio_evento
        ).total_seconds()

        print()

        print(
            "Primeira anomalia:",
            primeira_anomalia.fim
        )

        print(
            "Tempo de detecção:",
            atraso,
            "segundos"
        )

    assert primeira_anomalia is not None