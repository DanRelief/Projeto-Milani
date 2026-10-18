from pathlib import Path

from src.domain.measurement import (
    ParametroVital,
)

from src.infrastructure.ingestion.leitor_csv import (
    LeitorCSV,
)


PASTA_DADOS = (
    Path(__file__).parent
    / "dados"
)

ARQUIVO_CSV = (
    PASTA_DADOS
    / "sinais_vitais_simulados_15min.csv"
)


def carregar_medicoes():
    leitor = LeitorCSV()

    return leitor.ler(
        caminho_arquivo=ARQUIVO_CSV,
        id_paciente="PACIENTE_TESTE",
        id_sessao="INTEGRIDADE_CSV",
    )


def filtrar_parametro(
    medicoes,
    parametro,
):
    return [
        medicao
        for medicao in medicoes
        if medicao.parametro == parametro
    ]


def calcular_inclinacao_temporal(
    medicoes,
):
    """
    Calcula a tendência linear simples
    em unidades do parâmetro por minuto.

    Não usa FeatureExtractor nem qualquer
    componente de IA.
    """

    if len(medicoes) < 2:
        return 0.0

    medicoes = sorted(
        medicoes,
        key=lambda medicao: medicao.data_hora,
    )

    instante_inicial = (
        medicoes[0].data_hora
    )

    tempos = [
        (
            medicao.data_hora
            - instante_inicial
        ).total_seconds() / 60.0
        for medicao in medicoes
    ]

    valores = [
        medicao.valor
        for medicao in medicoes
    ]

    media_tempo = (
        sum(tempos)
        / len(tempos)
    )

    media_valores = (
        sum(valores)
        / len(valores)
    )

    numerador = sum(
        (
            tempo
            - media_tempo
        )
        * (
            valor
            - media_valores
        )
        for tempo, valor
        in zip(
            tempos,
            valores,
        )
    )

    denominador = sum(
        (
            tempo
            - media_tempo
        ) ** 2
        for tempo in tempos
    )

    if denominador == 0:
        return 0.0

    return (
        numerador
        / denominador
    )

def test_csv_estavel_quantidade_e_duracao():

    medicoes = carregar_medicoes()

    timestamps = sorted(
        {
            medicao.data_hora
            for medicao in medicoes
        }
    )

    duracao_segundos = (
        timestamps[-1]
        - timestamps[0]
    ).total_seconds()

    print()
    print(
        "INTEGRIDADE — QUANTIDADE"
    )
    print(
        "-----------------------"
    )

    print(
        "Medições:",
        len(medicoes)
    )

    print(
        "Instantes:",
        len(timestamps)
    )

    print(
        "Duração:",
        duracao_segundos,
        "segundos"
    )

    assert len(medicoes) == 543

    assert len(timestamps) == 181

    assert duracao_segundos == 900

def test_csv_estavel_nao_tem_gaps():

    medicoes = carregar_medicoes()

    timestamps = sorted(
        {
            medicao.data_hora
            for medicao in medicoes
        }
    )

    intervalos = [
        (
            atual
            - anterior
        ).total_seconds()
        for anterior, atual
        in zip(
            timestamps,
            timestamps[1:],
        )
    ]

    print()
    print(
        "INTEGRIDADE — INTERVALOS"
    )
    print(
        "------------------------"
    )

    print(
        "Menor intervalo:",
        min(intervalos),
        "s"
    )

    print(
        "Maior intervalo:",
        max(intervalos),
        "s"
    )

    intervalos_invalidos = [
        intervalo
        for intervalo in intervalos
        if intervalo != 5
    ]

    print(
        "Intervalos inválidos:",
        len(intervalos_invalidos)
    )

    assert len(
        intervalos_invalidos
    ) == 0

def test_csv_estavel_tem_tres_parametros_por_instante():

    medicoes = carregar_medicoes()

    medicoes_por_instante = {}

    for medicao in medicoes:

        if (
            medicao.data_hora
            not in medicoes_por_instante
        ):
            medicoes_por_instante[
                medicao.data_hora
            ] = []

        medicoes_por_instante[
            medicao.data_hora
        ].append(
            medicao
        )

    parametros_esperados = {
        ParametroVital.SPO2,
        ParametroVital.TEMPERATURA,
        ParametroVital.PRESSAO_ARTERIAL_MEDIA,
    }

    instantes_invalidos = []

    for (
        data_hora,
        medicoes_instante,
    ) in medicoes_por_instante.items():

        parametros_encontrados = {
            medicao.parametro
            for medicao
            in medicoes_instante
        }

        if (
            len(medicoes_instante) != 3
            or
            parametros_encontrados
            != parametros_esperados
        ):
            instantes_invalidos.append(
                data_hora
            )

    print()
    print(
        "INTEGRIDADE — COMPLETUDE"
    )
    print(
        "------------------------"
    )

    print(
        "Instantes analisados:",
        len(medicoes_por_instante)
    )

    print(
        "Instantes incompletos:",
        len(instantes_invalidos)
    )

    assert len(
        instantes_invalidos
    ) == 0

def test_csv_estavel_amplitudes():

    medicoes = carregar_medicoes()

    configuracoes = {
        ParametroVital.SPO2: {
            "nome": "SpO2",
            "amplitude_maxima": 1.5,
        },

        ParametroVital.TEMPERATURA: {
            "nome": "Temperatura",
            "amplitude_maxima": 0.8,
        },

        ParametroVital.PRESSAO_ARTERIAL_MEDIA: {
            "nome": "PAM",
            "amplitude_maxima": 8.0,
        },
    }

    print()
    print(
        "INTEGRIDADE — AMPLITUDE"
    )
    print(
        "-----------------------"
    )

    for (
        parametro,
        configuracao,
    ) in configuracoes.items():

        medicoes_parametro = (
            filtrar_parametro(
                medicoes,
                parametro,
            )
        )

        valores = [
            medicao.valor
            for medicao
            in medicoes_parametro
        ]

        minimo = min(valores)
        maximo = max(valores)

        media = (
            sum(valores)
            / len(valores)
        )

        amplitude = (
            maximo
            - minimo
        )

        print()

        print(
            configuracao["nome"]
        )

        print(
            "Mínimo:",
            minimo
        )

        print(
            "Média:",
            round(
                media,
                4,
            )
        )

        print(
            "Máximo:",
            maximo
        )

        print(
            "Amplitude:",
            round(
                amplitude,
                4,
            )
        )

        assert (
            amplitude
            <= configuracao[
                "amplitude_maxima"
            ]
        )

def test_csv_estavel_nao_tem_tendencia_forte():

    medicoes = carregar_medicoes()

    configuracoes = {
        ParametroVital.SPO2: {
            "nome": "SpO2",
            "inclinacao_maxima": 0.10,
        },

        ParametroVital.TEMPERATURA: {
            "nome": "Temperatura",
            "inclinacao_maxima": 0.05,
        },

        ParametroVital.PRESSAO_ARTERIAL_MEDIA: {
            "nome": "PAM",
            "inclinacao_maxima": 0.50,
        },
    }

    print()
    print(
        "INTEGRIDADE — TENDÊNCIA"
    )
    print(
        "-----------------------"
    )

    for (
        parametro,
        configuracao,
    ) in configuracoes.items():

        medicoes_parametro = (
            filtrar_parametro(
                medicoes,
                parametro,
            )
        )

        inclinacao = (
            calcular_inclinacao_temporal(
                medicoes_parametro
            )
        )

        print(
            configuracao["nome"],
            "→",
            round(
                inclinacao,
                6,
            ),
            "por minuto"
        )

        assert (
            abs(inclinacao)
            <= configuracao[
                "inclinacao_maxima"
            ]
        )