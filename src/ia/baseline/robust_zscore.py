from dataclasses import dataclass

from src.ia.baseline.rolling import BaselineStats



@dataclass
class RobustZScoreResult:
    valor_atual_valor: float

    baseline_mediana: float
    baseline_mad: float

    robust_zscore: float | None

    computable: bool

def calculate_robust_zscore(valor_atual_valor: float, baseline: BaselineStats) -> RobustZScoreResult:

    if baseline.mad == 0:

        return RobustZScoreResult(
            valor_atual_valor=valor_atual_valor,

            baseline_mediana=( baseline.mediana),

            baseline_mad=(baseline.mad),

            robust_zscore=None,

            computable=False,
        )

    scaled_mad = (1.4826 * baseline.mad)

    robust_zscore = (valor_atual_valor - baseline.mediana) / scaled_mad

    return RobustZScoreResult(
        valor_atual_valor=valor_atual_valor,

        baseline_mediana=(baseline.mediana),

        baseline_mad=(baseline.mad),

        robust_zscore=robust_zscore,

        computable=True,
    )
