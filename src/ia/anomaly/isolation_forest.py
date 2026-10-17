from dataclasses import dataclass

from sklearn.ensemble import IsolationForest


@dataclass(frozen=True)
class ResultadoAnomalia:
    anomalia: bool

    # Quanto maior este valor, mais anômalo
    # consideramos o exemplo.
    pontuacao_anomalia: float

    previsao_modelo: int


class DetectorIsolationForest:

    def __init__(self,numero_arvores: int = 200,contaminacao: str | float = "auto",semente: int = 42,):
        self.modelo = IsolationForest(n_estimators=numero_arvores,contamination=contaminacao,random_state=semente,n_jobs=-1,)

        self.treinado = False

    def treinar(self,vetores: list[list[float]]) -> None:

        if len(vetores) < 20:
            raise ValueError(
                "São necessárias pelo menos "
                "20 amostras para treinamento."
            )

        self.modelo.fit(vetores)

        self.treinado = True

    def avaliar(self,vetor: list[float]) -> ResultadoAnomalia:

        if not self.treinado:
            raise RuntimeError("O Isolation Forest ainda não foi treinado.")

        previsao = int(self.modelo.predict([vetor])[0])

        pontuacao_decisao = float(self.modelo.decision_function([vetor])[0])

        # No sklearn:
        # valores menores indicam maior anormalidade.
        # Invertemos apenas para facilitar nossa leitura:
        # maior pontuacao_anomalia = mais anômalo.
        pontuacao_anomalia = (-pontuacao_decisao)

        return ResultadoAnomalia(
            anomalia=(previsao == -1),

            pontuacao_anomalia=(pontuacao_anomalia),

            previsao_modelo=previsao,
        )