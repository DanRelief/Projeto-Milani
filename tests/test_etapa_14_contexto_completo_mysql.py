from src.ia.llm.construtor_contexto import (
    ConstrutorContextoRelatorio,
)


ID_SESSAO_TESTE = (
    "232d3234-0501-4ae4-9376-5cd7e10ec365"
)


def test_construir_contexto_completo_mysql():

    construtor = (
        ConstrutorContextoRelatorio()
    )

    contexto = construtor.construir(
        id_sessao=ID_SESSAO_TESTE,
    )

    assert (
        contexto.sessao.id_sessao
        == ID_SESSAO_TESTE
    )

    assert contexto.paciente.nome

    assert (
        contexto.responsaveis
        .responsavel_animal
    )

    assert len(
        contexto.procedimentos
    ) >= 1

    assert len(
        contexto.medicacoes
    ) >= 1

    assert len(
        contexto.historico
    ) >= 4

    print()
    print(
        "CONTEXTO COMPLETO DA SESSÃO"
    )
    print(
        "==========================="
    )

    print(
        "Paciente:",
        contexto.paciente.nome,
    )

    print(
        "Espécie:",
        contexto.paciente.especie,
    )

    print(
        "Porte:",
        contexto.paciente.porte,
    )

    print(
        "Responsável:",
        contexto.responsaveis
        .responsavel_animal,
    )

    print(
        "Aluno responsável:",
        contexto.responsaveis
        .aluno_responsavel,
    )

    print()
    print(
        "Procedimentos:",
        len(
            contexto.procedimentos
        ),
    )

    for procedimento in (
        contexto.procedimentos
    ):

        print(
            "-",
            procedimento.nome,
            "| executado por:",
            procedimento.executado_por,
        )

    print()
    print(
        "Medicações:",
        len(
            contexto.medicacoes
        ),
    )

    for medicacao in (
        contexto.medicacoes
    ):

        print(
            "-",
            medicacao.nome,
            medicacao.quantidade,
            medicacao.unidade,
            "| administrado por:",
            medicacao.administrado_por,
        )

    print()
    print(
        "Alertas:",
        len(
            contexto.alertas
        ),
    )

    print()
    print(
        "LINHA DO TEMPO"
    )
    print(
        "--------------"
    )

    for evento in contexto.historico:

        print(
            evento.data_hora.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            "-",
            evento.titulo,
            "|",
            evento.descricao,
        )