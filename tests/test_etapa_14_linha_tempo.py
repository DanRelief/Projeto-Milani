from datetime import datetime

from src.ia.llm.construtor_linha_tempo import (
    construir_linha_tempo,
)

from ia.llm.modelos_contexto import (
    AlertaRelatorio,
    ContextoRelatorio,
    DadosPacienteRelatorio,
    DadosResponsaveisRelatorio,
    DadosSessaoRelatorio,
    MedicacaoRelatorio,
    ProcedimentoRelatorio,
)


def test_construir_linha_tempo_ordenada():

    paciente = DadosPacienteRelatorio(
        id_paciente="DOG_001",
        nome="Ana",
        especie="Canina",
        idade=5,
        porte="Médio",
    )

    responsaveis = (
        DadosResponsaveisRelatorio(
            responsavel_animal="Maria",
            aluno_responsavel="Bryan",
        )
    )

    sessao = DadosSessaoRelatorio(
        id_sessao="SESSAO_001",
        inicio=datetime(
            2026,
            10,
            18,
            14,
            0,
            0,
        ),
        fim=datetime(
            2026,
            10,
            18,
            14,
            30,
            0,
        ),
        estado_geral="normal",
    )

    procedimentos = [
        ProcedimentoRelatorio(
            nome="Monitoramento anestésico",
            data_hora=datetime(
                2026,
                10,
                18,
                14,
                5,
                0,
            ),
            executado_por=(
                "Equipe veterinária"
            ),
            registrado_por="Bryan",
        )
    ]

    medicacoes = [
        MedicacaoRelatorio(
            nome="Medicamento de teste",
            quantidade=2.0,
            unidade="ml",
            data_hora=datetime(
                2026,
                10,
                18,
                14,
                10,
                0,
            ),
            administrado_por=(
                "Equipe veterinária"
            ),
            registrado_por="Bryan",
        )
    ]

    alertas = [
        AlertaRelatorio(
            parametro="spo2",
            nome_parametro="SpO₂",
            tipo_evento="abertura",
            data_hora=datetime(
                2026,
                10,
                18,
                14,
                15,
                0,
            ),
            valor=95.0,
            unidade="%",
            z_robusto=-20.0,
            motivo=(
                "Queda persistente detectada."
            ),
        ),

        AlertaRelatorio(
            parametro="spo2",
            nome_parametro="SpO₂",
            tipo_evento="encerramento",
            data_hora=datetime(
                2026,
                10,
                18,
                14,
                20,
                0,
            ),
            valor=98.0,
            unidade="%",
            z_robusto=0.2,
            motivo=(
                "Sinal retornou ao estado normal."
            ),
        ),
    ]

    contexto = ContextoRelatorio(
        paciente=paciente,
        responsaveis=responsaveis,
        sessao=sessao,
        data_hora_geracao=datetime(
            2026,
            10,
            18,
            14,
            30,
            0,
        ),
        procedimentos=procedimentos,
        medicacoes=medicacoes,
        alertas=alertas,
    )

    linha_tempo = construir_linha_tempo(
        contexto
    )

    assert len(linha_tempo) == 6

    assert (
        linha_tempo[0].tipo
        == "inicio_sessao"
    )

    assert (
        linha_tempo[-1].tipo
        == "fim_sessao"
    )

    horarios = [
        evento.data_hora
        for evento in linha_tempo
    ]

    assert horarios == sorted(
        horarios
    )

    titulos = [
        evento.titulo
        for evento in linha_tempo
    ]

    assert (
        "Procedimento registrado"
        in titulos
    )

    assert (
        "Medicação registrada"
        in titulos
    )

    assert (
        "Alerta aberto"
        in titulos
    )

    assert (
        "Alerta encerrado"
        in titulos
    )

    print()
    print(
        "LINHA DO TEMPO DA SESSÃO"
    )
    print(
        "------------------------"
    )

    for evento in linha_tempo:

        print(
            evento.data_hora.strftime(
                "%H:%M:%S"
            ),
            "-",
            evento.titulo,
            "|",
            evento.descricao,
        )