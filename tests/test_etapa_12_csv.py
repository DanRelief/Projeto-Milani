from pathlib import Path

from src.domain.measurement import (
    FonteDados,
    ParametroVital,
)

from src.infrastructure.ingestion.leitor_csv import (
    LeitorCSV,
)
from src.application.buffering.vital_buffer import (
    VitalBuffer,
)

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


def test_csv_estavel_15_minutos():

    caminho = (
        PASTA_DADOS
        / "sinais_vitais_simulados_15min.csv"
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=caminho,
        id_paciente="1",
        id_sessao="CSV_ESTAVEL",
    )

    spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    temperatura = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.TEMPERATURA
    ]

    pressao = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.PRESSAO_ARTERIAL_MEDIA
    ]

    print()
    print("CSV ESTÁVEL — 15 MIN")
    print("--------------------")
    print("Total:", len(medicoes))
    print("SpO2:", len(spo2))
    print("Temperatura:", len(temperatura))
    print("Pressão:", len(pressao))

    assert len(medicoes) == 543

    assert len(spo2) == 181
    assert len(temperatura) == 181
    assert len(pressao) == 181


def test_csv_evento_20_minutos():

    caminho = (
        PASTA_DADOS
        / "sinais_vitais_simulados_parada_cardiaca_20min.csv"
    )

    leitor = LeitorCSV()

    medicoes = leitor.ler(
        caminho_arquivo=caminho,
        id_paciente="1",
        id_sessao="CSV_EVENTO",
    )

    spo2 = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.SPO2
    ]

    temperatura = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.TEMPERATURA
    ]

    pressao = [
        medicao
        for medicao in medicoes
        if medicao.parametro
        == ParametroVital.PRESSAO_ARTERIAL_MEDIA
    ]

    print()
    print("CSV EVENTO — 20 MIN")
    print("-------------------")

    print(
        "Total:",
        len(medicoes)
    )

    print(
        "SpO2:",
        len(spo2)
    )

    print(
        "Temperatura:",
        len(temperatura)
    )

    print(
        "Pressão:",
        len(pressao)
    )

