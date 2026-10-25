from PySide6.QtCore import QObject, Signal

from src.infrastructure.repositories.repositorio_alertas import (
    RepositorioAlertas,
)

from ...domain.measurement import (
    Medicao,
    ParametroVital,
)

from ...ia.baseline.rolling import (
    calculate_rolling_baseline,
)

from ...ia.baseline.robust_zscore import (
    calculate_robust_zscore,
)

from ...ia.rules.motor_regras import (
    ConfiguracaoRegra,
    DirecaoAlteracao,
    EstadoMonitoramento,
    MotorRegraParametro,
)

from ...ia.alertas.motor_alerta import (
    EntradaMotorAlertas,
    MotorAlertas,
)

from ..buffering.vital_buffer import (
    VitalBuffer,
)
from src.infrastructure.repositories.repositorio_medicoes import (
    RepositorioMedicoes,
)


class ControladorMonitoramento(QObject):

    medicoes_atualizadas = Signal(object)

    spo2_atualizada = Signal(float)
    temperatura_atualizada = Signal(float)
    pam_atualizada = Signal(float)

    evento_alerta_gerado = Signal(object)

    analise_parametro_atualizada = Signal(object)
    resumo_monitoramento_atualizado = Signal(object)

    def __init__(self,parent=None,repositorio_alertas=None, repositorio_medicoes=None,):
        super().__init__(parent)

        self.repositorio_alertas = (
            repositorio_alertas
            if repositorio_alertas is not None
            else RepositorioAlertas()
        )

        self.repositorio_medicoes = (
            repositorio_medicoes
            if repositorio_medicoes is not None
            else RepositorioMedicoes()
        )

        self.id_paciente = None
        self.id_sessao = None

        self.buffer = None

        self.motor_alertas = MotorAlertas()

        self.regras = (
            self._criar_regras()
        )

        self.ultimos_valores = (
            self._criar_ultimos_valores()
        )

        self.analises_atuais = {}
    # -------------------------------------------------
    # CONFIGURAÇÕES
    # -------------------------------------------------

    @staticmethod
    def _criar_regras():
        return {
            ParametroVital.SPO2:
                MotorRegraParametro(
                    ConfiguracaoRegra(
                        limiar_entrada_z=3.0,
                        limiar_saida_z=1.5,
                        janelas_persistencia=3,
                        janelas_recuperacao=2,
                        qualidade_minima=0.8,
                        direcao=(
                            DirecaoAlteracao.QUEDA
                        ),
                    )
                ),

            ParametroVital.PRESSAO_ARTERIAL_MEDIA:
                MotorRegraParametro(
                    ConfiguracaoRegra(
                        limiar_entrada_z=3.0,
                        limiar_saida_z=1.5,
                        janelas_persistencia=3,
                        janelas_recuperacao=2,
                        qualidade_minima=0.8,
                        direcao=(
                            DirecaoAlteracao.QUEDA
                        ),
                    )
                ),

            ParametroVital.TEMPERATURA:
                MotorRegraParametro(
                    ConfiguracaoRegra(
                        limiar_entrada_z=3.0,
                        limiar_saida_z=1.5,
                        janelas_persistencia=3,
                        janelas_recuperacao=2,
                        qualidade_minima=0.8,
                        direcao=(
                            DirecaoAlteracao.AMBAS
                        ),
                    )
                ),
        }

    @staticmethod
    def _criar_ultimos_valores():
        return {
            ParametroVital.SPO2: None,
            ParametroVital.TEMPERATURA: None,
            ParametroVital.PRESSAO_ARTERIAL_MEDIA: None,
        }

    # -------------------------------------------------
    # SESSÃO
    # -------------------------------------------------

    def iniciar_sessao(
        self,
        id_paciente: str,
        id_sessao: str,
    ) -> None:

        self.id_paciente = id_paciente
        self.id_sessao = id_sessao

        self.buffer = VitalBuffer(
            id_paciente=id_paciente,
            id_sessao=id_sessao,
            max_minutes=30,
        )

        self.regras = (
            self._criar_regras()
        )

        self.motor_alertas = (
            MotorAlertas()
        )

        self.ultimos_valores = (
            self._criar_ultimos_valores()
        )

        self.analises_atuais = {}

    # -------------------------------------------------
    # ENTRADA DAS MEDIÇÕES
    # -------------------------------------------------

    def processar_medicoes(
        self,
        medicoes: list[Medicao],
    ) -> None:

        if not medicoes:
            return

        if self.buffer is None:
            return

        self._persistir_medicoes(medicoes)

        for medicao in medicoes:

            self.buffer.add(
                medicao
            )

            self.ultimos_valores[
                medicao.parametro
            ] = medicao.valor

            self._emitir_valor_atual(
                medicao
            )

            if (
                medicao.parametro
                in self.regras
            ):
                self._analisar_parametro(
                    medicao
                )

        self.medicoes_atualizadas.emit(
            medicoes
        )

        self._emitir_resumo_monitoramento()

    # -------------------------------------------------
    # VALORES PARA OS CARDS
    # -------------------------------------------------

    def _emitir_valor_atual(
        self,
        medicao: Medicao,
    ) -> None:

        if (
            medicao.parametro
            == ParametroVital.SPO2
        ):
            self.spo2_atualizada.emit(
                float(medicao.valor)
            )

        elif (
            medicao.parametro
            == ParametroVital.TEMPERATURA
        ):
            self.temperatura_atualizada.emit(
                float(medicao.valor)
            )

        elif (
            medicao.parametro
            == ParametroVital.PRESSAO_ARTERIAL_MEDIA
        ):
            self.pam_atualizada.emit(
                float(medicao.valor)
            )

    # -------------------------------------------------
    # PIPELINE GENÉRICO
    # -------------------------------------------------

    def _analisar_parametro(
        self,
        medicao: Medicao,
    ) -> None:

        parametro = medicao.parametro

        janela = self.buffer.get_recent(
            parametro=parametro,
            minutes=5,
        )

        if len(janela) < 6:

            analise = {
                "parametro": parametro,
                "nome": self._nome_parametro(
                    parametro
                ),
                "unidade": medicao.unidade,
                "status": "aquecimento",
                "amostras": len(janela),
                "valor": medicao.valor,
            }

            self.analises_atuais[
                parametro
            ] = analise

            self.analise_parametro_atualizada.emit(
                analise
            )

            return

        try:

            baseline = (
                calculate_rolling_baseline(
                    measurements=janela,
                    exclude_valor_atual=True,
                    minimo_samples=5,
                )
            )

        except ValueError:

            return

        resultado_z = (
            calculate_robust_zscore(
                valor_atual_valor=(
                    medicao.valor
                ),
                baseline=baseline,
            )
        )

        regra = self.regras[
            parametro
        ]

        resultado_regra = (
            regra.processar(
                z_robusto=(
                    resultado_z.robust_zscore
                ),
                qualidade_sinal=(
                    medicao.qualidade_sinal
                ),
            )
        )

        if resultado_regra.dados_validos:

            status = (
                resultado_regra
                .estado
                .value
            )

        else:

            status = "indisponivel"

        analise = {
            "parametro": parametro,

            "nome": self._nome_parametro(
                parametro
            ),

            "unidade": medicao.unidade,

            "status": status,

            "estado_regra": (
                resultado_regra
                .estado
                .value
            ),

            "valor": medicao.valor,

            "mediana": (
                baseline.mediana
            ),

            "mad": (
                baseline.mad
            ),

            "z_robusto": (
                resultado_z
                .robust_zscore
            ),

            "qualidade_sinal": (
                medicao.qualidade_sinal
            ),

            "motivo": (
                resultado_regra.motivo
            ),

            "dados_validos": (
                resultado_regra
                .dados_validos
            ),
        }

        self.analises_atuais[
            parametro
        ] = analise

        self.analise_parametro_atualizada.emit(
            analise
        )

        self._processar_alerta(
            medicao=medicao,
            resultado_z=resultado_z,
            resultado_regra=resultado_regra,
        )

    # -------------------------------------------------
    # MOTOR DE ALERTAS
    # -------------------------------------------------

    def _processar_alerta(
        self,
        medicao,
        resultado_z,
        resultado_regra,
    ) -> None:

        entrada = EntradaMotorAlertas(
            id_paciente=(
                medicao.id_paciente
            ),

            id_sessao=(
                medicao.id_sessao
            ),

            parametro=(
                medicao.parametro
            ),

            data_hora=(
                medicao.data_hora
            ),

            estado=(
                resultado_regra.estado
            ),

            valor_atual=(
                medicao.valor
            ),

            z_robusto=(
                resultado_z.robust_zscore
            ),

            qualidade_sinal=(
                medicao.qualidade_sinal
            ),

            motivo_regra=(
                resultado_regra.motivo
            ),

            dados_validos=(
                resultado_regra.dados_validos
            ),
        )

        evento = (
            self.motor_alertas.processar(
                entrada
            )
        )

        if evento is not None:

            self._persistir_evento_alerta(evento)

            self.evento_alerta_gerado.emit(evento)

    # -------------------------------------------------
    # RESUMO DOS TRÊS PARÂMETROS
    # -------------------------------------------------

    def _emitir_resumo_monitoramento(
        self,
    ) -> None:

        if not self.analises_atuais:
            return

        status_geral = (
            self._determinar_status_geral()
        )

        resumo = {
            "status_geral": status_geral,
            "analises": dict(
                self.analises_atuais
            ),
        }

        self.resumo_monitoramento_atualizado.emit(
            resumo
        )

    def _determinar_status_geral(
        self,
    ) -> str:

        estados = {
            analise["status"]
            for analise
            in self.analises_atuais.values()
        }

        if (
            EstadoMonitoramento.ALERTA.value
            in estados
        ):
            return "alerta"

        if (
            EstadoMonitoramento.RECUPERACAO.value
            in estados
        ):
            return "recuperacao"

        if (
            EstadoMonitoramento.OBSERVACAO.value
            in estados
        ):
            return "observacao"

        if (
            "indisponivel"
            in estados
        ):
            return "indisponivel"

        if (
            "aquecimento"
            in estados
        ):
            return "aquecimento"

        return "normal"

    # -------------------------------------------------
    # NOMES
    # -------------------------------------------------

    @staticmethod
    def _nome_parametro(
        parametro: ParametroVital,
    ) -> str:

        nomes = {
            ParametroVital.SPO2:
                "SpO₂",

            ParametroVital.TEMPERATURA:
                "Temperatura",

            ParametroVital.PRESSAO_ARTERIAL_MEDIA:
                "PAM",
        }

        return nomes.get(
            parametro,
            parametro.value,
        )
    def _persistir_evento_alerta(self,evento) -> None:

        try:
            self.repositorio_alertas.salvar(
                evento
            )

        except Exception as erro:
            print(
                "[M.I.S.A] Falha ao persistir "
                f"evento de alerta: {erro}"
            )

    def _persistir_medicoes(self,medicoes: list[Medicao],) -> None:
        try:
            self.repositorio_medicoes.salvar_lote(
                medicoes
            )

        except Exception as erro:
            print(
                "[M.I.S.A] Falha ao persistir "
                f"medições: {erro}"
            )