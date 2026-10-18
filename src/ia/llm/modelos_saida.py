from pydantic import BaseModel, Field


class RelatorioGemini(BaseModel):
    resumo_geral: str = Field(
        description=(
            "Resumo objetivo da sessão de monitoramento, "
            "baseado exclusivamente nos dados fornecidos."
        )
    )

    evolucao_sinais: list[str] = Field(
        default_factory=list,
        description=(
            "Principais alterações e tendências observadas "
            "nos sinais vitais."
        ),
    )

    eventos_relevantes: list[str] = Field(
        default_factory=list,
        description=(
            "Eventos relevantes registrados durante a sessão, "
            "incluindo alertas, procedimentos e medicações."
        ),
    )

    relacoes_temporais: list[str] = Field(
        default_factory=list,
        description=(
            "Relações temporais entre eventos, sem afirmar "
            "causalidade clínica não comprovada."
        ),
    )

    informacoes_ausentes: list[str] = Field(
        default_factory=list,
        description=(
            "Informações que seriam úteis para compreender "
            "melhor a sessão, mas que não estão disponíveis."
        ),
    )

    observacoes: list[str] = Field(
        default_factory=list,
        description=(
            "Observações adicionais baseadas nos registros."
        ),
    )

    aviso: str = Field(
        description=(
            "Aviso de que o relatório é apoio à interpretação "
            "e não substitui avaliação veterinária."
        )
    )