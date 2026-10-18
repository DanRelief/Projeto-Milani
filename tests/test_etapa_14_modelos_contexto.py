from datetime import datetime

from ia.llm.modelos_contexto import (
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


def test_criar_contexto_completo_relatorio():

    inicio_sessao = datetime(
        2026,
        10,
        18,
        14,
        0,
        0,
    )

    paciente = DadosPacienteRelatorio(
        id_paciente="DOG_001",
        nome="Ana",
        especie="Canina",
        idade=5,
        porte="Médio",
        estado_clinico="Estável",
    )

    responsaveis = (
        DadosResponsaveisRelatorio(
            responsavel_animal="Maria",
            aluno_responsavel="Bryan",
            professor_responsavel="Milani",
        )
    )

    sessao = DadosSessaoRelatorio(
        id_sessao="SESSAO_001",
        inicio=inicio_sessao,
        estado_geral="alerta",
    )

    analises = [
        AnaliseParametroRelatorio(
            parametro="spo2",
            nome="SpO₂",
            valor_atual=95.0,
            unidade="%",
            mediana_baseline=98.0,
            mad_baseline=0.1,
            z_robusto=-20.0,
            estado="alerta",
            qualidade_sinal=1.0,
            motivo=(
                "Queda persistente detectada."
            ),
        ),
        AnaliseParametroRelatorio(
            parametro="temperatura",
            nome="Temperatura",
            valor_atual=37.5,
            unidade="°C",
            mediana_baseline=37.5,
            mad_baseline=0.02,
            z_robusto=0.0,
            estado="normal",
            qualidade_sinal=1.0,
        ),
    ]

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
            executado_por="Equipe veterinária",
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
        )
    ]

    resumo_sinais = [
        ResumoSerieVitalRelatorio(
            parametro="spo2",
            nome="SpO₂",
            unidade="%",
            quantidade_medicoes=180,
            valor_inicial=98.0,
            valor_final=95.0,
            minimo=94.8,
            maximo=98.3,
            media=97.5,
            mediana=97.8,
            quantidade_alertas=1,
        )
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
            20,
            0,
        ),
        analises_atuais=analises,
        resumo_sinais=resumo_sinais,
        procedimentos=procedimentos,
        medicacoes=medicacoes,
        alertas=alertas,
    )

    assert contexto.paciente.nome == "Ana"

    assert (
        contexto.responsaveis
        .aluno_responsavel
        == "Bryan"
    )

    assert (
        contexto.sessao.id_sessao
        == "SESSAO_001"
    )

    assert len(
        contexto.analises_atuais
    ) == 2

    assert len(
        contexto.procedimentos
    ) == 1

    assert len(
        contexto.medicacoes
    ) == 1

    assert len(
        contexto.alertas
    ) == 1

    assert len(
        contexto.resumo_sinais
    ) == 1

    # O histórico ainda será criado
    # pela Etapa 14.2.
    assert contexto.historico == []

    print()
    print(
        "CONTEXTO COMPLETO DO RELATÓRIO"
    )
    print(
        "-----------------------------"
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
        "Aluno responsável:",
        contexto.responsaveis
        .aluno_responsavel,
    )

    print(
        "Estado geral:",
        contexto.sessao.estado_geral,
    )

    print(
        "Análises:",
        len(
            contexto.analises_atuais
        ),
    )

    print(
        "Procedimentos:",
        len(
            contexto.procedimentos
        ),
    )

    print(
        "Medicações:",
        len(
            contexto.medicacoes
        ),
    )

    print(
        "Alertas:",
        len(
            contexto.alertas
        ),
    )