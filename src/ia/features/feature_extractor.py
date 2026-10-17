from dataclasses import dataclass
from src.domain.measurement import Medicao,ParametroVital
from src.ia.features.statistical import (
    calculate_delta,
    calculate_max,
    calculate_media,
    calculate_mediana,
    calculate_min,
    calculate_desvio_padrao,
)
from src.ia.features.trend import calculate_inclinacao

@dataclass
class CaracteristicasJanela:
    parametro: ParametroVital
    window_minutes: float

    count: int

    valor_atual: float

    media: float
    mediana: float

    minimo: float
    maximo: float

    desvio_padrao: float
    delta: float
    inclinacao: float


class FeatureExtractor:

    def extract(self,measurements: list[Medicao],window_minutes: float,) -> CaracteristicasJanela:

        if not measurements:
            raise ValueError(
                "Não há medições para extrair features."
            )

        parametro = measurements[0].parametro

        for Medicao in measurements:
            if Medicao.parametro != parametro:
                raise ValueError(
                    "Todas as medições da janela devem "
                    "pertencer ao mesmo parâmetro."
                )

        values = [
            Medicao.valor
            for Medicao in measurements
        ]

        return CaracteristicasJanela(
            parametro=parametro,
            window_minutes=window_minutes,

            count=len(values),

            valor_atual=values[-1],

            media=calculate_media(values),
            mediana=calculate_mediana(values),

            minimo=calculate_min(values),
            maximo=calculate_max(values),

            desvio_padrao=calculate_desvio_padrao(values),
            delta=calculate_delta(values),

            inclinacao=calculate_inclinacao(
                measurements
            ),
        )