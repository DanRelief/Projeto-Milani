from dataclasses import dataclass
from enum import Enum


class EstadoMonitoramento(str, Enum):
    NORMAL = "normal"
    OBSERVACAO = "observacao"
    ALERTA = "alerta"
    RECUPERACAO = "recuperacao"

class DirecaoAlteracao(str, Enum):
    QUEDA = "queda"
    AUMENTO = "aumento"
    AMBAS = "ambas"

@dataclass
class ConfiguracaoRegra:
    limiar_entrada_z: float = 3.0
    limiar_saida_z: float = 1.5

    janelas_persistencia: int = 3
    janelas_recuperacao: int = 2

    qualidade_minima: float = 0.8

    direcao: DirecaoAlteracao = DirecaoAlteracao.AMBAS


@dataclass
class ResultadoRegra:
    estado: EstadoMonitoramento

    alteracao_detectada: bool

    contador_persistencia: int
    contador_recuperacao: int

    dados_validos: bool

    motivo: str

class MotorRegraParametro:

    def __init__(self,configuracao: ConfiguracaoRegra | None = None,):
        self.configuracao = (configuracao if configuracao is not None else ConfiguracaoRegra())

        self.estado = (EstadoMonitoramento.NORMAL)

        self.contador_persistencia = 0
        self.contador_recuperacao = 0

    def processar(self,z_robusto: float | None,qualidade_sinal: float | None,) -> ResultadoRegra:

        if qualidade_sinal is not None:
            if (qualidade_sinal < self.configuracao.qualidade_minima):
                return ResultadoRegra(
                    estado=self.estado,
                    alteracao_detectada=False,
                    contador_persistencia=(self.contador_persistencia),
                    contador_recuperacao=(self.contador_recuperacao),
                    dados_validos=False,motivo=("Qualidade do sinal insuficiente."),
                )

        if z_robusto is None:
            return ResultadoRegra(estado=self.estado,alteracao_detectada=False,
                                  contador_persistencia=(self.contador_persistencia),
                                  contador_recuperacao=(self.contador_recuperacao),
                                  dados_validos=False,
                                  motivo=("Robust Z-Score não calculável."),
            )

        magnitude_z = abs(z_robusto)

        alteracao = (self.esta_em_alteracao(z_robusto))

        recuperado = (self.esta_recuperado(z_robusto))

        self._atualizar_estado(alteracao=alteracao,recuperado=recuperado,)

        return ResultadoRegra(
            estado=self.estado,
            alteracao_detectada=alteracao,
            contador_persistencia=(self.contador_persistencia),
            contador_recuperacao=(self.contador_recuperacao),
            dados_validos=True,
            motivo=self._gerar_motivo(z_robusto),
        )

    def _atualizar_estado(self,alteracao: bool,recuperado: bool,) -> None:

        if (self.estado == EstadoMonitoramento.NORMAL):
            if alteracao:
                self.contador_persistencia = 1
                self.estado = (EstadoMonitoramento.OBSERVACAO)

            return
        
        if (self.estado== EstadoMonitoramento.OBSERVACAO):
            if alteracao:
                self.contador_persistencia += 1
                if (self.contador_persistencia >= self.configuracao.janelas_persistencia):
                    self.estado = (EstadoMonitoramento.ALERTA)
                    self.contador_recuperacao = 0

            else:
                self.contador_persistencia = 0
                self.estado = (EstadoMonitoramento.NORMAL)

            return
        
        if (self.estado== EstadoMonitoramento.ALERTA):
            if recuperado:
                self.contador_recuperacao = 1
                self.estado = (EstadoMonitoramento.RECUPERACAO)

            return
        
        if (self.estado == EstadoMonitoramento.RECUPERACAO):
            if recuperado:

                self.contador_recuperacao += 1

                if (self.contador_recuperacao >= self.configuracao.janelas_recuperacao):

                    self.estado = (EstadoMonitoramento.NORMAL)

                    self.contador_persistencia = 0
                    self.contador_recuperacao = 0

            elif alteracao:

                self.estado = (EstadoMonitoramento.ALERTA)
                self.contador_recuperacao = 0
                
    def _gerar_motivo(self,z_robusto: float,) -> str:
        return (
            f"Robust Z-Score = "
            f"{z_robusto:.2f}; "
            f"estado = {self.estado.value}."
        )
    
    def esta_em_alteracao(self,z_robusto: float,) -> bool:

        direcao = (self.configuracao.direcao)

        limiar = (self.configuracao.limiar_entrada_z)

        if direcao == DirecaoAlteracao.QUEDA:

            return (z_robusto <= -limiar)

        if direcao == DirecaoAlteracao.AUMENTO:

            return (z_robusto >= limiar)

        return (abs(z_robusto) >= limiar)

    def esta_recuperado(self,z_robusto: float,) -> bool:

        direcao = (self.configuracao.direcao)

        limiar = (self.configuracao.limiar_saida_z)

        if direcao == DirecaoAlteracao.QUEDA:

            return (z_robusto >= -limiar)

        if direcao == DirecaoAlteracao.AUMENTO:

            return (z_robusto <= limiar)

        return (abs(z_robusto) <= limiar)