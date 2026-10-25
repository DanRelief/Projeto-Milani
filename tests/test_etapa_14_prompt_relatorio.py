from datetime import datetime

from src.ia.llm.construtor_prompt import (
    construir_prompt_relatorio,
    contexto_para_json,
)

from src.ia.llm.modelos_contexto import (
    AlertaRelatorio,
    ContextoRelatorio,
    DadosPacienteRelatorio,
    DadosResponsaveisRelatorio,
    DadosSessaoRelatorio,
    MedicacaoRelatorio,
    ProcedimentoRelatorio,
    ResumoSerieVitalRelatorio,
)


def criar_contexto_teste():

    paciente = DadosPacienteRelatorio(
        id_paciente="1",
        nome="Ana",
        especie="Cão",
        idade=10,
        porte="pequeno",
        estado_clinico="estavel",
    )

    responsaveis = (
        DadosResponsaveisRelatorio(
            responsavel_animal="Bryan",
            aluno_responsavel="Bryan",
        )
    )

    sessao = DadosSessaoRelatorio(
        id_sessao="SESSAO_TESTE",
        inicio=datetime(
            2026,
            10,
            18,
            16,
            15,
            32,
        ),
        fim=datetime(
            2026,
            10,
            18,
            16,
            17,
            23,
        ),
        estado_geral="encerrada",
    )

    procedimento = ProcedimentoRelatorio(
        nome="Desvio de Cepto",
        data_hora=datetime(
            2026,
            10,
            18,
            16,
            15,
            40,
        ),
        executado_por="Bryan",
        registrado_por="Bryan",
    )

    medicacao = MedicacaoRelatorio(
        nome="Dipirona",
        data_hora=datetime(
            2026,
            10,
            18,
            16,
            16,
            0,
        ),
        quantidade=15.0,
        unidade="mg",
        administrado_por="Fabiola",
        registrado_por="Bryan",
    )

    alerta = AlertaRelatorio(
        parametro="spo2",
        nome_parametro="SpO₂",
        tipo_evento="abertura",
        data_hora=datetime(
            2026,
            10,
            18,
            16,
            16,
            20,
        ),
        valor=94.0,
        unidade="%",
        z_robusto=-5.3,
        motivo=(
            "Queda persistente detectada."
        ),
    )

    resumo_spo2 = (
        ResumoSerieVitalRelatorio(
            parametro="spo2",
            nome="SpO₂",
            unidade="%",
            quantidade_medicoes=120,
            valor_inicial=98.01,
            valor_final=93.03,
            minimo=93.03,
            maximo=98.47,
            media=96.804,
            mediana=97.785,
            quantidade_alertas=1,
        )
    )

    return ContextoRelatorio(
        paciente=paciente,
        responsaveis=responsaveis,
        sessao=sessao,
        data_hora_geracao=datetime.now(),
        resumo_sinais=[
            resumo_spo2
        ],
        procedimentos=[
            procedimento
        ],
        medicacoes=[
            medicacao
        ],
        alertas=[
            alerta
        ],
    )


def test_contexto_e_serializado():

    contexto = criar_contexto_teste()

    json_contexto = contexto_para_json(
        contexto
    )

    assert '"Ana"' in json_contexto
    assert '"Dipirona"' in json_contexto

    assert (
        '"quantidade_medicoes": 120'
        in json_contexto
    )

    assert (
        '"tipo_evento": "abertura"'
        in json_contexto
    )

    print()
    print(
        "JSON DO CONTEXTO"
    )
    print(
        "================"
    )

    print(
        json_contexto
    )


def test_prompt_contem_regras_e_contexto():

    contexto = criar_contexto_teste()

    prompt = construir_prompt_relatorio(
        contexto
    )

    assert "Não invente" in prompt

    assert (
        "Não faça diagnóstico"
        in prompt
    )

    assert (
        "não causal"
        in prompt.lower()
    )

    assert "Ana" in prompt
    assert "Dipirona" in prompt
    assert "SpO₂" in prompt

    print()
    print(
        "PROMPT GERADO"
    )
    print(
        "=============="
    )

    print(
        prompt[:2000]
    )