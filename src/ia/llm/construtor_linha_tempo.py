from src.ia.llm.modelos_contexto import (
    AlertaRelatorio,
    ContextoRelatorio,
    EventoHistoricoRelatorio,
    MedicacaoRelatorio,
    ProcedimentoRelatorio,
)


def criar_evento_inicio_sessao(
    contexto: ContextoRelatorio,
) -> EventoHistoricoRelatorio:

    return EventoHistoricoRelatorio(
        tipo="inicio_sessao",
        data_hora=contexto.sessao.inicio,
        titulo="Sessão de monitoramento iniciada",
        descricao=(
            f"Monitoramento iniciado para "
            f"{contexto.paciente.nome}."
        ),
        origem="sistema",
    )


def criar_evento_fim_sessao(
    contexto: ContextoRelatorio,
) -> EventoHistoricoRelatorio | None:

    if contexto.sessao.fim is None:
        return None

    return EventoHistoricoRelatorio(
        tipo="fim_sessao",
        data_hora=contexto.sessao.fim,
        titulo="Sessão de monitoramento encerrada",
        descricao=(
            f"Monitoramento encerrado para "
            f"{contexto.paciente.nome}."
        ),
        origem="sistema",
    )


def converter_procedimento(
    procedimento: ProcedimentoRelatorio,
) -> EventoHistoricoRelatorio:

    descricao = procedimento.nome

    if procedimento.executado_por:
        descricao += (
            f" | Executado por: "
            f"{procedimento.executado_por}"
        )

    if procedimento.observacao:
        descricao += (
            f" | Observação: "
            f"{procedimento.observacao}"
        )

    return EventoHistoricoRelatorio(
        tipo="procedimento",
        data_hora=procedimento.data_hora,
        titulo="Procedimento registrado",
        descricao=descricao,
        origem="usuario",
        registrado_por=(
            procedimento.registrado_por
        ),
    )


def converter_medicacao(
    medicacao: MedicacaoRelatorio,
) -> EventoHistoricoRelatorio:

    descricao = medicacao.nome

    if (
        medicacao.quantidade is not None
        and medicacao.unidade
    ):
        descricao += (
            f" | Quantidade: "
            f"{medicacao.quantidade} "
            f"{medicacao.unidade}"
        )

    if medicacao.administrado_por:
        descricao += (
            f" | Administrado por: "
            f"{medicacao.administrado_por}"
        )

    if medicacao.observacao:
        descricao += (
            f" | Observação: "
            f"{medicacao.observacao}"
        )

    return EventoHistoricoRelatorio(
        tipo="medicacao",
        data_hora=medicacao.data_hora,
        titulo="Medicação registrada",
        descricao=descricao,
        origem="usuario",
        registrado_por=(
            medicacao.registrado_por
        ),
    )


def converter_alerta(
    alerta: AlertaRelatorio,
) -> EventoHistoricoRelatorio:

    descricao = (
        f"{alerta.nome_parametro}"
    )

    if alerta.valor is not None:
        descricao += (
            f" | Valor: "
            f"{alerta.valor:.2f}"
        )

        if alerta.unidade:
            descricao += (
                f" {alerta.unidade}"
            )

    if alerta.z_robusto is not None:
        descricao += (
            f" | Z robusto: "
            f"{alerta.z_robusto:.2f}"
        )

    if alerta.motivo:
        descricao += (
            f" | Motivo: "
            f"{alerta.motivo}"
        )

    tipo_evento = (
        alerta.tipo_evento.lower()
    )

    if tipo_evento == "abertura":
        titulo = "Alerta aberto"

    elif tipo_evento == "encerramento":
        titulo = "Alerta encerrado"

    else:
        titulo = (
            f"Evento de alerta: "
            f"{alerta.tipo_evento}"
        )

    return EventoHistoricoRelatorio(
        tipo="alerta",
        data_hora=alerta.data_hora,
        titulo=titulo,
        descricao=descricao,
        parametro=alerta.parametro,
        origem="motor_alertas",
    )


def construir_linha_tempo(
    contexto: ContextoRelatorio,
) -> list[EventoHistoricoRelatorio]:

    eventos = []

    eventos.append(
        criar_evento_inicio_sessao(
            contexto
        )
    )

    for procedimento in contexto.procedimentos:
        eventos.append(
            converter_procedimento(
                procedimento
            )
        )

    for medicacao in contexto.medicacoes:
        eventos.append(
            converter_medicacao(
                medicacao
            )
        )

    for alerta in contexto.alertas:
        eventos.append(
            converter_alerta(
                alerta
            )
        )

    evento_fim = criar_evento_fim_sessao(
        contexto
    )

    if evento_fim is not None:
        eventos.append(
            evento_fim
        )

    eventos.sort(
        key=lambda evento: evento.data_hora
    )

    return eventos