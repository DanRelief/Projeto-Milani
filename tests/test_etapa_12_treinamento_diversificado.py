import random

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from src.infrastructure.ingestion.leitor_csv import (
    LeitorCSV,
)
from src.domain.measurement import (
    ParametroVital,
)

from src.ia.anomaly.construtor_dataset import (
    criar_amostras_janelas,
    criar_dataset_janelas,
)

from src.ia.anomaly.vetor_caracteristicas import (
    criar_vetor_relativo,
)

from src.ia.anomaly.isolation_forest import (
    DetectorIsolationForest,
)

from src.ia.features.feature_extractor import (
    FeatureExtractor,
)

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)
PASTA_DADOS = (
    Path(__file__).parent
    / "dados"
)

ARQUIVO_CSV_ESTAVEL = (
    PASTA_DADOS
    / "sinais_vitais_simulados_15min.csv"
)

ARQUIVO_CSV_EVENTO = (
    PASTA_DADOS
    / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
)

@dataclass(frozen=True)
class PerfilTreinamentoSpO2:
    baseline_spo2: float
    amplitude_spo2: float
    desvio_ruido_spo2: float
    tendencia_spo2_por_minuto: float


def gerar_perfis_estaveis(
    quantidade: int,
    semente: int,
):
    aleatorio = random.Random(
        semente
    )

    perfis = []

    for _ in range(quantidade):

        perfil = PerfilTreinamentoSpO2(
            baseline_spo2=(
                aleatorio.uniform(
                    97.2,
                    98.8,
                )
            ),

            amplitude_spo2=(
                aleatorio.uniform(
                    0.15,
                    0.35,
                )
            ),

            desvio_ruido_spo2=(
                aleatorio.uniform(
                    0.08,
                    0.25,
                )
            ),

            tendencia_spo2_por_minuto=(
                aleatorio.uniform(
                    -0.02,
                    0.02,
                )
            ),
        )

        perfis.append(
            perfil
        )

    return perfis

def gerar_spo2_com_perfil(
    perfil,
    semente: int,
    id_sessao: str,
):
    simulador = SimuladorSinaisVitais(
        id_paciente="DOG_TREINO",
        id_sessao=id_sessao,
        seed=semente,

        baseline_spo2=(
            perfil.baseline_spo2
        ),

        amplitude_spo2=(
            perfil.amplitude_spo2
        ),

        desvio_ruido_spo2=(
            perfil.desvio_ruido_spo2
        ),

        tendencia_spo2_por_minuto=(
            perfil.tendencia_spo2_por_minuto
        ),
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

def criar_dataset_treinamento_diversificado(
    extrator,
    funcao_vetor,
):
    perfis = gerar_perfis_estaveis(
        quantidade=40,
        semente=1000,
    )

    dataset = []

    for indice, perfil in enumerate(
        perfis
    ):

        medicoes = gerar_spo2_com_perfil(
            perfil=perfil,
            semente=10000 + indice,
            id_sessao=(
                f"TREINO_DIVERSO_{indice}"
            ),
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

def criar_dataset_validacao_diversificado(
    extrator,
    funcao_vetor,
):
    perfis = gerar_perfis_estaveis(
        quantidade=20,
        semente=2000,
    )

    dataset = []

    for indice, perfil in enumerate(
        perfis
    ):

        medicoes = gerar_spo2_com_perfil(
            perfil=perfil,
            semente=20000 + indice,
            id_sessao=(
                f"VALIDACAO_{indice}"
            ),
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

def test_isolation_forest_diversificado_validacao():

    extrator = FeatureExtractor()

    dataset_treinamento = (
        criar_dataset_treinamento_diversificado(
            extrator,
            criar_vetor_relativo,
        )
    )

    dataset_validacao = (
        criar_dataset_validacao_diversificado(
            extrator,
            criar_vetor_relativo,
        )
    )

    detector = DetectorIsolationForest(
        numero_arvores=200,
        semente=42,
    )

    detector.treinar(
        dataset_treinamento
    )

    resultados = [
        detector.avaliar(
            vetor
        )
        for vetor
        in dataset_validacao
    ]

    quantidade_anomalias = sum(
        resultado.anomalia
        for resultado in resultados
    )

    taxa = (
        quantidade_anomalias
        / len(resultados)
    )

    pontuacoes = [
        resultado.pontuacao_anomalia
        for resultado in resultados
    ]

    print()
    print(
        "ISOLATION FOREST — "
        "TREINAMENTO DIVERSIFICADO"
    )
    print(
        "------------------------------------"
    )

    print(
        "Janelas treinamento:",
        len(dataset_treinamento)
    )

    print(
        "Janelas validação:",
        len(dataset_validacao)
    )

    print(
        "Anomalias validação:",
        quantidade_anomalias
    )

    print(
        "Taxa:",
        round(
            taxa * 100,
            2
        ),
        "%"
    )

    print()

    print(
        "Score mínimo:",
        min(pontuacoes)
    )

    print(
        "Score médio:",
        (
            sum(pontuacoes)
            / len(pontuacoes)
        )
    )

    print(
        "Score máximo:",
        max(pontuacoes)
    )

    assert len(
        dataset_treinamento
    ) > 0

    assert len(
        dataset_validacao
    ) > 0


def separar_segmentos_continuos(
    medicoes,
    intervalo_maximo_segundos: float = 15.0,
):
    medicoes = sorted(
        medicoes,
        key=lambda medicao: medicao.data_hora,
    )

    if not medicoes:
        return []

    segmentos = [
        [medicoes[0]]
    ]

    for medicao in medicoes[1:]:

        anterior = segmentos[-1][-1]

        intervalo = (
            medicao.data_hora
            - anterior.data_hora
        ).total_seconds()

        if intervalo > intervalo_maximo_segundos:

            segmentos.append(
                [medicao]
            )

        else:

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

def criar_detector_diversificado():

    extrator = FeatureExtractor()

    dataset_treinamento = (
        criar_dataset_treinamento_diversificado(
            extrator,
            criar_vetor_relativo,
        )
    )

    detector = DetectorIsolationForest(
        numero_arvores=200,
        semente=42,
    )

    detector.treinar(
        dataset_treinamento
    )

    return detector, extrator

def test_diversificado_csv_estavel():

    detector, extrator = (
        criar_detector_diversificado()
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=ARQUIVO_CSV_ESTAVEL,
        id_paciente="PACIENTE_CSV_ESTAVEL",
        id_sessao="CSV_ESTAVEL",
    )

    amostras = criar_amostras_csv(
        medicoes=medicoes,
        extrator=extrator,
        funcao_vetor=criar_vetor_relativo,
    )

    resultados = [
        detector.avaliar(
            amostra.vetor
        )
        for amostra in amostras
    ]

    quantidade_anomalias = sum(
        resultado.anomalia
        for resultado in resultados
    )

    taxa = (
        quantidade_anomalias
        / len(resultados)
        if resultados
        else 0.0
    )

    pontuacoes = [
        resultado.pontuacao_anomalia
        for resultado in resultados
    ]

    print()
    print(
        "ISOLATION FOREST DIVERSIFICADO"
    )
    print(
        "CSV ESTÁVEL EXTERNO"
    )
    print(
        "============================="
    )

    print(
        "Janelas:",
        len(amostras)
    )

    print(
        "Anomalias:",
        quantidade_anomalias
    )

    print(
        "Taxa:",
        round(
            taxa * 100,
            2
        ),
        "%"
    )

    print()

    print(
        "Score mínimo:",
        min(pontuacoes)
    )

    print(
        "Score médio:",
        sum(pontuacoes)
        / len(pontuacoes)
    )

    print(
        "Score máximo:",
        max(pontuacoes)
    )

    assert len(amostras) > 0

def separar_fases_evento(
    amostras,
    inicio_deterioracao,
    inicio_parada,
    inicio_recuperacao,
):
    estabilidade = []
    transicao = []
    deterioracao = []
    recuperacao = []

    for amostra in amostras:

        if amostra.fim < inicio_deterioracao:

            estabilidade.append(
                amostra
            )

        elif (
            amostra.inicio
            < inicio_deterioracao
            <= amostra.fim
        ):

            transicao.append(
                amostra
            )

        elif (
            amostra.inicio
            >= inicio_deterioracao
            and amostra.fim
            < inicio_parada
        ):

            deterioracao.append(
                amostra
            )

        elif (
            amostra.inicio
            >= inicio_recuperacao
        ):

            recuperacao.append(
                amostra
            )

    return {
        "estabilidade": estabilidade,
        "transicao": transicao,
        "deterioracao": deterioracao,
        "recuperacao": recuperacao,
    }

def test_diversificado_csv_evento():

    detector, extrator = (
        criar_detector_diversificado()
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=ARQUIVO_CSV_EVENTO,
        id_paciente="PACIENTE_CSV_EVENTO",
        id_sessao="CSV_EVENTO",
    )

    amostras = criar_amostras_csv(
        medicoes=medicoes,
        extrator=extrator,
        funcao_vetor=criar_vetor_relativo,
    )

    medicoes_spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    inicio = min(
        medicao.data_hora
        for medicao in medicoes_spo2
    )

    inicio_deterioracao = (
        inicio
        + timedelta(minutes=7)
    )

    inicio_parada = (
        inicio
        + timedelta(minutes=12)
    )

    inicio_recuperacao = (
        inicio
        + timedelta(minutes=15)
    )

    fases = separar_fases_evento(
        amostras=amostras,
        inicio_deterioracao=inicio_deterioracao,
        inicio_parada=inicio_parada,
        inicio_recuperacao=inicio_recuperacao,
    )

    print()
    print(
        "ISOLATION FOREST DIVERSIFICADO"
    )
    print(
        "CSV EVENTO"
    )
    print(
        "============================="
    )

    for nome_fase, amostras_fase in (
        fases.items()
    ):

        resultados = [
            detector.avaliar(
                amostra.vetor
            )
            for amostra
            in amostras_fase
        ]

        anomalias = sum(
            resultado.anomalia
            for resultado in resultados
        )

        taxa = (
            anomalias
            / len(resultados)
            if resultados
            else 0.0
        )

        print(
            nome_fase,
            ":",
            anomalias,
            "/",
            len(resultados),
            "-",
            round(
                taxa * 100,
                2
            ),
            "%"
        )

    assert len(amostras) > 0