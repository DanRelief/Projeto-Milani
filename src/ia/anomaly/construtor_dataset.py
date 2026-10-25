from src.ia.anomaly.vetor_caracteristicas import criar_vetor_caracteristicas
from dataclasses import dataclass
from datetime import datetime

def criar_dataset_janelas(medicoes,extrator_caracteristicas,tamanho_janela: int = 61,passo: int = 6,funcao_vetor=criar_vetor_caracteristicas) -> list[list[float]]:

    if len(medicoes) < tamanho_janela:
        return []

    dataset = []

    for inicio in range(0,len(medicoes) - tamanho_janela + 1,passo,):

        fim = (inicio + tamanho_janela
        )

        janela = medicoes[inicio:fim]

        caracteristicas = (extrator_caracteristicas.extract(janela,window_minutes=5,))

        vetor = funcao_vetor(caracteristicas)

        dataset.append(vetor)

    return dataset

@dataclass(frozen=True)
class AmostraJanela:
    vetor: list[float]
    inicio: datetime
    fim: datetime


def criar_amostras_janelas(medicoes,extrator_caracteristicas,tamanho_janela: int = 61,passo: int = 6,funcao_vetor=criar_vetor_caracteristicas,) -> list[AmostraJanela]:

    if len(medicoes) < tamanho_janela:
        return []

    amostras = []

    for inicio_indice in range(
        0,
        len(medicoes) - tamanho_janela + 1,
        passo,
    ):

        fim_indice = (
            inicio_indice
            + tamanho_janela
        )

        janela = medicoes[
            inicio_indice:fim_indice
        ]

        caracteristicas = (
            extrator_caracteristicas.extract(
                janela,
                window_minutes=5,
            )
        )

        vetor = funcao_vetor(
            caracteristicas
        )

        amostras.append(
            AmostraJanela(
                vetor=vetor,
                inicio=janela[0].data_hora,
                fim=janela[-1].data_hora,
            )
        )

    return amostras