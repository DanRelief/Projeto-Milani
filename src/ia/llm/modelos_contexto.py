from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DadosPacienteRelatorio:
    id_paciente: str

    nome: str
    especie: str

    idade: int | None = None
    porte: str | None = None

    estado_clinico: str | None = None


@dataclass
class DadosResponsaveisRelatorio:
    responsavel_animal: str | None = None

    aluno_responsavel: str | None = None

    professor_responsavel: str | None = None

    veterinario_responsavel: str | None = None


@dataclass
class DadosSessaoRelatorio:
    id_sessao: str

    inicio: datetime

    fim: datetime | None = None

    estado_geral: str | None = None


@dataclass
class AnaliseParametroRelatorio:
    parametro: str
    nome: str

    valor_atual: float
    unidade: str

    mediana_baseline: float | None = None
    mad_baseline: float | None = None

    z_robusto: float | None = None

    estado: str = "indisponivel"

    qualidade_sinal: float | None = None

    motivo: str | None = None


@dataclass
class ResumoSerieVitalRelatorio:
    parametro: str
    nome: str
    unidade: str

    quantidade_medicoes: int

    valor_inicial: float | None = None
    valor_final: float | None = None

    minimo: float | None = None
    maximo: float | None = None

    media: float | None = None
    mediana: float | None = None

    quantidade_alertas: int = 0


@dataclass
class ProcedimentoRelatorio:
    nome: str

    data_hora: datetime

    executado_por: str | None = None
    registrado_por: str | None = None

    observacao: str | None = None


@dataclass
class MedicacaoRelatorio:
    nome: str

    data_hora: datetime

    quantidade: float | None = None
    unidade: str | None = None

    administrado_por: str | None = None
    registrado_por: str | None = None

    observacao: str | None = None


@dataclass
class AlertaRelatorio:
    parametro: str
    nome_parametro: str

    tipo_evento: str

    data_hora: datetime

    valor: float | None = None
    unidade: str | None = None

    z_robusto: float | None = None

    motivo: str | None = None


@dataclass
class EventoHistoricoRelatorio:
    tipo: str

    data_hora: datetime

    titulo: str

    descricao: str | None = None

    parametro: str | None = None

    origem: str | None = None

    registrado_por: str | None = None


@dataclass
class ContextoRelatorio:
    paciente: DadosPacienteRelatorio

    responsaveis: DadosResponsaveisRelatorio

    sessao: DadosSessaoRelatorio

    data_hora_geracao: datetime

    analises_atuais: list[
        AnaliseParametroRelatorio
    ] = field(
        default_factory=list
    )

    resumo_sinais: list[
        ResumoSerieVitalRelatorio
    ] = field(
        default_factory=list
    )

    procedimentos: list[
        ProcedimentoRelatorio
    ] = field(
        default_factory=list
    )

    medicacoes: list[
        MedicacaoRelatorio
    ] = field(
        default_factory=list
    )

    alertas: list[
        AlertaRelatorio
    ] = field(
        default_factory=list
    )

    historico: list[
        EventoHistoricoRelatorio
    ] = field(
        default_factory=list
    )