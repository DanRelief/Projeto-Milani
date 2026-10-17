import random

from src.ia.anomaly.isolation_forest import DetectorIsolationForest


def test_isolation_forest():

    aleatorio = random.Random(42)

    dados_normais = []

    for _ in range(300):

        valor = aleatorio.gauss(
            98.0,
            0.15,
        )

        vetor = [
            valor,                       # atual
            aleatorio.gauss(98, 0.1),   # média
            aleatorio.gauss(98, 0.1),   # mediana
            aleatorio.gauss(97.7, 0.1), # mínimo
            aleatorio.gauss(98.3, 0.1), # máximo
            aleatorio.gauss(0.17, 0.03),# desvio
            aleatorio.gauss(0, 0.1),    # delta
            aleatorio.gauss(0, 0.03),   # inclinação
        ]

        dados_normais.append(
            vetor
        )

    detector = DetectorIsolationForest(numero_arvores=200,semente=42,)

    detector.treinar(dados_normais)

    vetor_normal = [
        98.0,
        98.02,
        98.01,
        97.75,
        98.25,
        0.16,
        -0.05,
        0.01,
    ]

    vetor_anormal = [
        93.5,
        95.5,
        95.8,
        93.4,
        98.0,
        1.8,
        -4.5,
        -1.0,
    ]

    resultado_normal = detector.avaliar(vetor_normal)

    resultado_anormal = detector.avaliar(vetor_anormal)

    print()
    print("ISOLATION FOREST")
    print("----------------")

    print("Normal:",resultado_normal)
    print("Anormal:",resultado_anormal)

    assert (resultado_anormal.pontuacao_anomalia > resultado_normal.pontuacao_anomalia)

    assert (resultado_anormal.anomalia is True)