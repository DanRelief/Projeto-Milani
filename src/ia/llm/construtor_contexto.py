from datetime import datetime

from src.domain.measurement import (
    ParametroVital,
)
from statistics import (
    mean,
    median,
)

from src.ia.llm.construtor_linha_tempo import (
    construir_linha_tempo,
)

from src.ia.llm.modelos_contexto import (
    AlertaRelatorio,
    AnaliseParametroRelatorio,
    ContextoRelatorio,
    DadosPacienteRelatorio,
    DadosResponsaveisRelatorio,
    DadosSessaoRelatorio,
    MedicacaoRelatorio,
    ProcedimentoRelatorio,
    ResumoSerieVitalRelatorio,
)

from src.infrastructure.repositories.repositorio_alertas import (
    RepositorioAlertas,
)
from src.infrastructure.repositories.repositorio_medicoes import (
    RepositorioMedicoes,
)

from src.infrastructure.repositories.repositorio_medicacoes import (
    RepositorioMedicacoes,
)

from src.infrastructure.repositories.repositorio_procedimentos import (
    RepositorioProcedimentos,
)

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)

class ConstrutorContextoRelatorio:

    def __init__(
        self,
        repositorio_sessoes=None,
        repositorio_alertas=None,
        repositorio_procedimentos=None,
        repositorio_medicacoes=None,
        repositorio_medicoes=None,
    ) -> None:

        self.repositorio_sessoes = (
            repositorio_sessoes
            if repositorio_sessoes is not None
            else RepositorioSessoes()
        )

        self.repositorio_alertas = (
            repositorio_alertas
            if repositorio_alertas is not None
            else RepositorioAlertas()
        )

        self.repositorio_procedimentos = (
            repositorio_procedimentos
            if repositorio_procedimentos is not None
            else RepositorioProcedimentos()
        )

        self.repositorio_medicacoes = (
            repositorio_medicacoes
            if repositorio_medicacoes is not None
            else RepositorioMedicacoes()
        )
        self.repositorio_medicoes = (
            repositorio_medicoes
            if repositorio_medicoes is not None
            else RepositorioMedicoes()
        )

    def construir(
        self,
        id_sessao: str,
        analises_atuais: dict | None = None,
    ) -> ContextoRelatorio:

        dados_sessao = (
            self.repositorio_sessoes
            .buscar_por_id(
                id_sessao
            )
        )

        if dados_sessao is None:
            raise ValueError(
                f"Sessão não encontrada: {id_sessao}"
            )

        paciente = (
            self._construir_paciente(
                dados_sessao
            )
        )

        responsaveis = (
            self._construir_responsaveis(
                dados_sessao
            )
        )

        sessao = (
            self._construir_sessao(
                dados_sessao
            )
        )

        procedimentos = (
            self._construir_procedimentos(
                id_sessao
            )
        )

        medicacoes = (
            self._construir_medicacoes(
                id_sessao
            )
        )

        alertas = (
            self._construir_alertas(
                id_sessao
            )
        )

        resumo_sinais = (
            self._construir_resumo_sinais(
                id_sessao=id_sessao,
                alertas=alertas,
            )
        )

        analises = (
            self._construir_analises(
                analises_atuais
                or {}
            )
        )

        contexto = ContextoRelatorio(
            paciente=paciente,
            responsaveis=responsaveis,
            sessao=sessao,
            data_hora_geracao=(datetime.now()),
            analises_atuais=analises,
            resumo_sinais=resumo_sinais,
            procedimentos=procedimentos,
            medicacoes=medicacoes,
            alertas=alertas,
        )

        contexto.historico = (
            construir_linha_tempo(
                contexto
            )
        )

        return contexto

    @staticmethod
    def _construir_paciente(
        dados: dict,
    ) -> DadosPacienteRelatorio:

        return DadosPacienteRelatorio(
            id_paciente=str(
                dados["animal_id"]
            ),
            nome=dados["animal_nome"],
            especie=dados["especie"],
            idade=dados["idade"],
            porte=dados["porte"],
            estado_clinico=(
                dados["estado_clinico"]
            ),
        )

    @staticmethod
    def _construir_responsaveis(
        dados: dict,
    ) -> DadosResponsaveisRelatorio:

        aluno_responsavel = None
        professor_responsavel = None

        papel = dados.get(
            "papel_iniciador"
        )

        if papel == "student":
            aluno_responsavel = (
                dados.get(
                    "nome_iniciador"
                )
            )

        elif papel == "teacher":
            professor_responsavel = (
                dados.get(
                    "nome_iniciador"
                )
            )

        return DadosResponsaveisRelatorio(
            responsavel_animal=(
                dados.get(
                    "nome_responsavel"
                )
            ),
            aluno_responsavel=(
                aluno_responsavel
            ),
            professor_responsavel=(
                professor_responsavel
            ),
        )

    @staticmethod
    def _construir_sessao(
        dados: dict,
    ) -> DadosSessaoRelatorio:

        return DadosSessaoRelatorio(
            id_sessao=(
                dados["sessao_id"]
            ),
            inicio=(
                dados["data_hora_inicio"]
            ),
            fim=(
                dados["data_hora_fim"]
            ),
            estado_geral=(
                dados["status"]
            ),
        )

    def _construir_procedimentos(
        self,
        id_sessao: str,
    ) -> list[ProcedimentoRelatorio]:

        registros = (
            self.repositorio_procedimentos
            .listar_por_sessao(
                id_sessao
            )
        )

        procedimentos = []

        for registro in registros:

            procedimentos.append(
                ProcedimentoRelatorio(
                    nome=registro["nome"],
                    data_hora=(
                        registro[
                            "data_hora"
                        ]
                    ),
                    executado_por=(
                        registro.get(
                            "executado_por"
                        )
                    ),
                    registrado_por=(
                        registro.get(
                            "nome_registrador"
                        )
                    ),
                    observacao=(
                        registro.get(
                            "observacao"
                        )
                    ),
                )
            )

        return procedimentos

    def _construir_medicacoes(
        self,
        id_sessao: str,
    ) -> list[MedicacaoRelatorio]:

        registros = (
            self.repositorio_medicacoes
            .listar_por_sessao(
                id_sessao
            )
        )

        medicacoes = []

        for registro in registros:

            medicacoes.append(
                MedicacaoRelatorio(
                    nome=registro["nome"],
                    data_hora=(
                        registro[
                            "data_hora"
                        ]
                    ),
                    quantidade=(
                        registro.get(
                            "quantidade"
                        )
                    ),
                    unidade=(
                        registro.get(
                            "unidade"
                        )
                    ),
                    administrado_por=(
                        registro.get(
                            "administrado_por"
                        )
                    ),
                    registrado_por=(
                        registro.get(
                            "nome_registrador"
                        )
                    ),
                    observacao=(
                        registro.get(
                            "observacao"
                        )
                    ),
                )
            )

        return medicacoes

    def _construir_alertas(
        self,
        id_sessao: str,
    ) -> list[AlertaRelatorio]:

        registros = (
            self.repositorio_alertas
            .listar_por_sessao(
                id_sessao
            )
        )

        alertas = []

        for registro in registros:

            parametro = (
                registro["parametro"]
            )

            alertas.append(
                AlertaRelatorio(
                    parametro=parametro,
                    nome_parametro=(
                        self._nome_parametro(
                            parametro
                        )
                    ),
                    tipo_evento=(
                        registro[
                            "tipo_evento"
                        ]
                    ),
                    data_hora=(
                        registro[
                            "data_hora"
                        ]
                    ),
                    valor=(
                        registro.get(
                            "valor_atual"
                        )
                    ),
                    unidade=(
                        self._unidade_parametro(
                            parametro
                        )
                    ),
                    z_robusto=(
                        registro.get(
                            "z_robusto"
                        )
                    ),
                    motivo=(
                        registro.get(
                            "motivo"
                        )
                    ),
                )
            )

        return alertas

    @staticmethod
    def _construir_analises(
        analises_atuais: dict,
    ) -> list[AnaliseParametroRelatorio]:

        analises = []

        for analise in (
            analises_atuais.values()
        ):

            parametro = analise.get(
                "parametro"
            )

            if isinstance(
                parametro,
                ParametroVital,
            ):
                valor_parametro = (
                    parametro.value
                )

            else:
                valor_parametro = str(
                    parametro
                )

            analises.append(
                AnaliseParametroRelatorio(
                    parametro=(
                        valor_parametro
                    ),
                    nome=analise.get(
                        "nome",
                        valor_parametro,
                    ),
                    valor_atual=analise.get(
                        "valor"
                    ),
                    unidade=analise.get(
                        "unidade",
                        "",
                    ),
                    mediana_baseline=(
                        analise.get(
                            "mediana"
                        )
                    ),
                    mad_baseline=(
                        analise.get(
                            "mad"
                        )
                    ),
                    z_robusto=(
                        analise.get(
                            "z_robusto"
                        )
                    ),
                    estado=analise.get(
                        "status",
                        "indisponivel",
                    ),
                    qualidade_sinal=(
                        analise.get(
                            "qualidade_sinal"
                        )
                    ),
                    motivo=analise.get(
                        "motivo"
                    ),
                )
            )

        return analises

    @staticmethod
    def _nome_parametro(
        parametro: str,
    ) -> str:

        nomes = {
            "spo2": "SpO₂",
            "temperatura": "Temperatura",
            "pressao_arterial_media": "PAM",
        }

        return nomes.get(
            parametro,
            parametro,
        )

    @staticmethod
    def _unidade_parametro(
        parametro: str,
    ) -> str | None:

        unidades = {
            "spo2": "%",
            "temperatura": "°C",
            "pressao_arterial_media": "mmHg",
        }

        return unidades.get(
            parametro
        )
    
    def _construir_resumo_sinais(self,id_sessao: str,alertas: list[AlertaRelatorio]) -> list[ResumoSerieVitalRelatorio]:

        registros = (
            self.repositorio_medicoes
            .listar_por_sessao(
                id_sessao
            )
        )

        medicoes_por_parametro = {}

        for registro in registros:

            parametro = registro[
                "parametro"
            ]

            if parametro not in (
                medicoes_por_parametro
            ):
                medicoes_por_parametro[
                    parametro
                ] = []

            medicoes_por_parametro[
                parametro
            ].append(
                registro
            )

        resumos = []

        for (
            parametro,
            medicoes,
        ) in medicoes_por_parametro.items():

            valores = [
                float(
                    medicao["valor"]
                )
                for medicao in medicoes
            ]

            if not valores:
                continue

            quantidade_alertas = sum(
                1
                for alerta in alertas
                if (
                    alerta.parametro
                    == parametro
                    and
                    alerta.tipo_evento
                    == "abertura"
                )
            )

            resumos.append(
                ResumoSerieVitalRelatorio(
                    parametro=parametro,
                    nome=(
                        self._nome_parametro(
                            parametro
                        )
                    ),
                    unidade=(
                        medicoes[0][
                            "unidade"
                        ]
                    ),
                    quantidade_medicoes=(
                        len(valores)
                    ),
                    valor_inicial=(
                        valores[0]
                    ),
                    valor_final=(
                        valores[-1]
                    ),
                    minimo=min(
                        valores
                    ),
                    maximo=max(
                        valores
                    ),
                    media=mean(
                        valores
                    ),
                    mediana=median(
                        valores
                    ),
                    quantidade_alertas=(
                        quantidade_alertas
                    ),
                )
            )

        ordem = {
            "spo2": 0,
            "temperatura": 1,
            "pressao_arterial_media": 2,
        }

        resumos.sort(
            key=lambda resumo: ordem.get(
                resumo.parametro,
                999,
            )
        )

        return resumos
