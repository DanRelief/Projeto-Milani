from dataclasses import dataclass


@dataclass(frozen=True)
class PerfilTreinamentoSpO2:
    deslocamento_baseline: float
    multiplicador_variacao: float
    tendencia_por_minuto: float


PERFIS_TREINAMENTO = [
    PerfilTreinamentoSpO2(
        deslocamento_baseline=-0.6,
        multiplicador_variacao=0.7,
        tendencia_por_minuto=0.00,
    ),
    PerfilTreinamentoSpO2(
        deslocamento_baseline=-0.3,
        multiplicador_variacao=1.0,
        tendencia_por_minuto=0.01,
    ),
    PerfilTreinamentoSpO2(
        deslocamento_baseline=0.0,
        multiplicador_variacao=1.0,
        tendencia_por_minuto=0.00,
    ),
    PerfilTreinamentoSpO2(
        deslocamento_baseline=0.3,
        multiplicador_variacao=1.2,
        tendencia_por_minuto=-0.01,
    ),
    PerfilTreinamentoSpO2(
        deslocamento_baseline=0.6,
        multiplicador_variacao=0.8,
        tendencia_por_minuto=0.00,
    ),
]