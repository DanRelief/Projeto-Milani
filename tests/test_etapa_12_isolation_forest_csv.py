from datetime import datetime
from pathlib import Path

from src.domain.measurement import (
    ParametroVital,
)

from src.ia.anomaly.construtor_dataset import (
    criar_amostras_janelas,
    criar_dataset_janelas,
)

from src.ia.anomaly.isolation_forest import (
    DetectorIsolationForest,
)

from src.ia.features.feature_extractor import (
    FeatureExtractor,
)

from src.infrastructure.ingestion.leitor_csv import (
    LeitorCSV,
)

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)
from src.ia.anomaly.vetor_caracteristicas import (
    criar_vetor_caracteristicas,
    criar_vetor_relativo,
)
PASTA_DADOS = (
    Path(__file__).parent
    / "dados"
)


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

NOMES_FEATURES_ABSOLUTAS = [
    "valor_atual",
    "media",
    "mediana",
    "minimo",
    "maximo",
    "desvio_padrao",
    "delta",
    "inclinacao",
]


NOMES_FEATURES_RELATIVAS = [
    "desvio_atual_relativo",
    "amplitude_relativa",
    "variabilidade_relativa",
    "delta_relativo",
    "inclinacao_relativa",
]

def mostrar_distribuicao_features(
    nome,
    vetores,
    nomes_features,
):
    print()
    print(nome)
    print("-" * len(nome))

    for indice, nome_feature in enumerate(
        nomes_features
    ):
        valores = [
            vetor[indice]
            for vetor in vetores
        ]

        media = (
            sum(valores)
            / len(valores)
        )

        minimo = min(valores)
        maximo = max(valores)

        print(
            f"{nome_feature:25} "
            f"min={minimo:10.6f} "
            f"media={media:10.6f} "
            f"max={maximo:10.6f}"
        )

def gerar_spo2_estavel(
    semente: int,
):
    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_TREINO",
        id_sessao=f"TREINO_{semente}",
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


def separar_segmentos_continuos(
    medicoes,
    intervalo_maximo_segundos=15,
):
    if not medicoes:
        return []

    medicoes = sorted(
        medicoes,
        key=lambda medicao: medicao.data_hora,
    )

    segmentos = [
        [medicoes[0]]
    ]

    for medicao in medicoes[1:]:

        anterior = segmentos[-1][-1]

        intervalo = (
            medicao.data_hora
            - anterior.data_hora
        ).total_seconds()

        if (
            intervalo
            > intervalo_maximo_segundos
        ):
            segmentos.append(
                []
            )

        segmentos[-1].append(
            medicao
        )

    return segmentos

def criar_amostras_csv(
    medicoes,
    extrator,
    funcao_vetor,
):
    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    segmentos = (
        separar_segmentos_continuos(
            medicoes_spo2
        )
    )

    amostras = []

    for segmento in segmentos:

        if len(segmento) < 61:
            continue

        amostras_segmento = (
            criar_amostras_janelas(
                medicoes=segmento,
                extrator_caracteristicas=extrator,
                tamanho_janela=61,
                passo=6,
                funcao_vetor=funcao_vetor,
            )
        )

        amostras.extend(
            amostras_segmento
        )

    return amostras


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

    return (
        quantidade,
        taxa,
    )

def test_isolation_forest_csv_estavel():

    extrator = FeatureExtractor()

    (
        detector,
        dataset_treinamento,
    ) = criar_detector(
        extrator,
        criar_vetor_caracteristicas,
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_15min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_ESTAVEL",
    )

    amostras = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_caracteristicas,
    )

    vetores_csv = [
    amostra.vetor
    for amostra in amostras
]

    mostrar_distribuicao_features(
        "TREINAMENTO",
        dataset_treinamento,
        NOMES_FEATURES_ABSOLUTAS,
    )

    mostrar_distribuicao_features(
        "CSV ESTÁVEL",
        vetores_csv,
        NOMES_FEATURES_ABSOLUTAS,
    )
    (
        quantidade,
        taxa,
    ) = contar_anomalias(
        detector,
        amostras,
    )
    resultados = [
    detector.avaliar(
        amostra.vetor
    )
    for amostra in amostras
]

    pontuacoes = [
        resultado.pontuacao_anomalia
        for resultado in resultados
    ]

    print()
    print(
        "Pontuação mínima:",
        min(pontuacoes)
    )

    print(
        "Pontuação média:",
        (
            sum(pontuacoes)
            / len(pontuacoes)
        )
    )

    print(
        "Pontuação máxima:",
        max(pontuacoes)
    )

    print()
    print(
        "ISOLATION FOREST — CSV ESTÁVEL"
    )
    print(
        "------------------------------"
    )

    print(
        "Janelas de treinamento:",
        len(dataset_treinamento)
    )

    print(
        "Janelas CSV:",
        len(amostras)
    )

    print(
        "Anomalias:",
        quantidade
    )

    print(
        "Taxa:",
        round(
            taxa * 100,
            2
        ),
        "%"
    )

    assert len(amostras) > 0

def test_isolation_forest_csv_evento():

    extrator = FeatureExtractor()

    (
        detector,
        dataset_treinamento,
    ) = criar_detector(
        extrator,
        criar_vetor_caracteristicas,
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_EVENTO",
    )

    amostras = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_caracteristicas,
    )

    antes = []
    deterioracao = []
    recuperacao = []

    for amostra in amostras:

        if (
            amostra.fim
            < INICIO_DETERIORACAO
        ):
            antes.append(
                amostra
            )

        elif (
            amostra.fim
            < INICIO_PARADA
        ):
            deterioracao.append(
                amostra
            )

        elif (
            amostra.fim
            >= INICIO_RECUPERACAO
        ):
            recuperacao.append(
                amostra
            )
    quantidade_antes, taxa_antes = (
        contar_anomalias(
            detector,
            antes,
        )
    )

    quantidade_deterioracao, taxa_deterioracao = (
        contar_anomalias(
            detector,
            deterioracao,
        )
    )

    quantidade_recuperacao, taxa_recuperacao = (
        contar_anomalias(
            detector,
            recuperacao,
        )
    )

    primeira_anomalia = None

    for amostra in deterioracao:

        resultado = detector.avaliar(
            amostra.vetor
        )

        if resultado.anomalia:

            primeira_anomalia = (
                amostra
            )

            break

    print()
    print(
        "ISOLATION FOREST — CSV EVENTO"
    )
    print(
        "-----------------------------"
    )

    print(
        "Janelas totais:",
        len(amostras)
    )

    print()

    print(
        "Estabilidade:",
        quantidade_antes,
        "/",
        len(antes),
        "-",
        round(
            taxa_antes * 100,
            2
        ),
        "%"
    )

    print(
        "Deterioração:",
        quantidade_deterioracao,
        "/",
        len(deterioracao),
        "-",
        round(
            taxa_deterioracao * 100,
            2
        ),
        "%"
    )

    print(
        "Recuperação:",
        quantidade_recuperacao,
        "/",
        len(recuperacao),
        "-",
        round(
            taxa_recuperacao * 100,
            2
        ),
        "%"
    )
    if primeira_anomalia is not None:

        atraso = (
            primeira_anomalia.fim
            - INICIO_DETERIORACAO
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

    else:

        print()
        print(
            "Nenhuma anomalia detectada "
            "durante a deterioração."
        )

    assert len(amostras) > 0

def criar_detector(
    extrator,
    funcao_vetor,
):

    dataset_treinamento = (
        criar_dataset_treinamento(
            extrator=extrator,
            funcao_vetor=funcao_vetor,
        )
    )

    detector = DetectorIsolationForest(
        numero_arvores=200,
        semente=42,
    )

    detector.treinar(
        dataset_treinamento
    )

    return (
        detector,
        dataset_treinamento,
    )

def criar_dataset_treinamento(
    extrator,
    funcao_vetor,
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
            funcao_vetor=funcao_vetor,
        )

        dataset.extend(
            vetores
        )

    return dataset

def test_comparar_v1_v2_csv_estavel():

    extrator = FeatureExtractor()
    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_15min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_ESTAVEL",
    )

    # =========================
    # V1 — ABSOLUTO
    # =========================

    detector_v1, treino_v1 = (
        criar_detector(
            extrator,
            criar_vetor_caracteristicas,
        )
    )

    amostras_v1 = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_caracteristicas,
    )

    quantidade_v1, taxa_v1 = (
        contar_anomalias(
            detector_v1,
            amostras_v1,
        )
    )

    # =========================
    # V2 — RELATIVO
    # =========================

    detector_v2, treino_v2 = (
        criar_detector(
            extrator,
            criar_vetor_relativo,
        )
    )

    amostras_v2 = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_relativo,
    )

    quantidade_v2, taxa_v2 = (
        contar_anomalias(
            detector_v2,
            amostras_v2,
        )
    )
    mostrar_distribuicao_features(
    "TREINAMENTO V2",
    treino_v2,
    NOMES_FEATURES_RELATIVAS,
)

    vetores_csv_v2 = [
        amostra.vetor
        for amostra in amostras_v2
    ]

    mostrar_distribuicao_features(
        "CSV ESTÁVEL V2",
        vetores_csv_v2,
        NOMES_FEATURES_RELATIVAS,
    )

    print()
    print("ISOLATION FOREST — CSV ESTÁVEL")
    print("==============================")

    print()
    print("V1 — ABSOLUTO")
    print("----------------")
    print(
        "Treinamento:",
        len(treino_v1)
    )
    print(
        "Janelas:",
        len(amostras_v1)
    )
    print(
        "Anomalias:",
        quantidade_v1
    )
    print(
        "Taxa:",
        round(taxa_v1 * 100, 2),
        "%"
    )

    print()
    print("V2 — RELATIVO")
    print("----------------")
    print(
        "Treinamento:",
        len(treino_v2)
    )
    print(
        "Janelas:",
        len(amostras_v2)
    )
    print(
        "Anomalias:",
        quantidade_v2
    )
    print(
        "Taxa:",
        round(taxa_v2 * 100, 2),
        "%"
    )
    pontuacoes_v2_estavel = resumir_pontuacoes(
        detector_v2,
        amostras_v2,
    )

    print()
    print(
        "SCORES V2 — CSV ESTÁVEL"
    )
    print(
        "-----------------------"
    )

    print(
        pontuacoes_v2_estavel
    )
    assert len(amostras_v1) > 0
    assert len(amostras_v2) > 0

def avaliar_fases(
    detector,
    amostras,
):
    estabilidade = []
    deterioracao = []
    recuperacao = []

    for amostra in amostras:

        if (
            amostra.fim
            < INICIO_DETERIORACAO
        ):
            estabilidade.append(
                amostra
            )

        elif (
            amostra.fim
            < INICIO_PARADA
        ):
            deterioracao.append(
                amostra
            )

        elif (
            amostra.fim
            >= INICIO_RECUPERACAO
        ):
            recuperacao.append(
                amostra
            )

    quantidade_estavel, taxa_estavel = (
        contar_anomalias(
            detector,
            estabilidade,
        )
    )

    quantidade_deterioracao, taxa_deterioracao = (
        contar_anomalias(
            detector,
            deterioracao,
        )
    )

    quantidade_recuperacao, taxa_recuperacao = (
        contar_anomalias(
            detector,
            recuperacao,
        )
    )

    return {
        "estabilidade": (
            quantidade_estavel,
            len(estabilidade),
            taxa_estavel,
        ),
        "deterioracao": (
            quantidade_deterioracao,
            len(deterioracao),
            taxa_deterioracao,
        ),
        "recuperacao": (
            quantidade_recuperacao,
            len(recuperacao),
            taxa_recuperacao,
        ),
    }

def resumir_pontuacoes(
    detector,
    amostras,
):

    if not amostras:
        return None

    pontuacoes = [
        detector.avaliar(
            amostra.vetor
        ).pontuacao_anomalia
        for amostra in amostras
    ]

    return {
        "minimo": min(pontuacoes),
        "media": (
            sum(pontuacoes)
            / len(pontuacoes)
        ),
        "maximo": max(pontuacoes),
    }

def test_comparar_v1_v2_csv_evento():

    extrator = FeatureExtractor()
    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=(
            PASTA_DADOS
            / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
        ),
        id_paciente="1",
        id_sessao="CSV_EVENTO_COMPARACAO",
    )

    # V1
    detector_v1, _ = criar_detector(
        extrator,
        criar_vetor_caracteristicas,
    )

    amostras_v1 = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_caracteristicas,
    )

    resultado_v1 = avaliar_fases(
        detector_v1,
        amostras_v1,
    )

    # V2
    detector_v2, _ = criar_detector(
        extrator,
        criar_vetor_relativo,
    )

    amostras_v2 = criar_amostras_csv(
        medicoes,
        extrator,
        criar_vetor_relativo,
    )

    resultado_v2 = avaliar_fases(
        detector_v2,
        amostras_v2,
    )
    (
    estabilidade_v2,
    deterioracao_v2,
    recuperacao_v2,
) = separar_fases(
    amostras_v2
)
    score_estavel = resumir_pontuacoes(
    detector_v2,
    estabilidade_v2,
)

    score_deterioracao = resumir_pontuacoes(
        detector_v2,
        deterioracao_v2,
    )
    print()
    print("SCORES V2")
    print("---------")

    print(
        "Estabilidade:",
        score_estavel
    )

    print(
        "Deterioração:",
        score_deterioracao
    )

    print()
    print(
        "ISOLATION FOREST — EVENTO V1 × V2"
    )
    print(
        "================================="
    )

    for nome_modelo, resultado in [
        ("V1 ABSOLUTO", resultado_v1),
        ("V2 RELATIVO", resultado_v2),
    ]:

        print()
        print(nome_modelo)
        print("-" * len(nome_modelo))

        for fase in [
            "estabilidade",
            "deterioracao",
            "recuperacao",
        ]:

            quantidade, total, taxa = (
                resultado[fase]
            )

            print(
                f"{fase:15} "
                f"{quantidade}/{total} "
                f"- {taxa * 100:.2f}%"
            )

    assert len(amostras_v1) > 0
    assert len(amostras_v2) > 0

def separar_fases(
    amostras,
):
    estabilidade = []
    deterioracao = []
    recuperacao = []

    for amostra in amostras:

        if amostra.fim < INICIO_DETERIORACAO:
            estabilidade.append(
                amostra
            )

        elif amostra.fim < INICIO_PARADA:
            deterioracao.append(
                amostra
            )

        elif amostra.fim >= INICIO_RECUPERACAO:
            recuperacao.append(
                amostra
            )

    return (
        estabilidade,
        deterioracao,
        recuperacao,
    )
