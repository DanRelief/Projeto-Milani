from src.infrastructure.database import (
    get_db_connection,
)

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)


def buscar_ultima_sessao():

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()

        cursor = conexao.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT id
            FROM sessoes_monitoramento
            ORDER BY criado_em DESC
            LIMIT 1
            """
        )

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if (
            conexao is not None
            and conexao.is_connected()
        ):
            conexao.close()


def test_buscar_contexto_basico_sessao():

    registro = buscar_ultima_sessao()

    assert registro is not None

    repositorio = (
        RepositorioSessoes()
    )

    sessao = repositorio.buscar_por_id(
        registro["id"]
    )

    assert sessao is not None

    assert sessao["sessao_id"]
    assert sessao["animal_id"]
    assert sessao["animal_nome"]
    assert sessao["especie"]
    assert sessao["nome_responsavel"]
    assert sessao["nome_iniciador"]

    print()
    print(
        "CONTEXTO BÁSICO DA SESSÃO"
    )
    print(
        "-------------------------"
    )

    print(
        "Sessão:",
        sessao["sessao_id"],
    )

    print(
        "Paciente:",
        sessao["animal_nome"],
    )

    print(
        "Espécie:",
        sessao["especie"],
    )

    print(
        "Responsável:",
        sessao["nome_responsavel"],
    )

    print(
        "Sessão iniciada por:",
        sessao["nome_iniciador"],
    )

    print(
        "Papel:",
        sessao["papel_iniciador"],
    )

    print(
        "Status:",
        sessao["status"],
    )