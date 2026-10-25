from datetime import datetime

import pytest

from src.infrastructure.database import (
    get_db_connection,
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


def buscar_animal_teste():
    """
    Busca um animal existente e o usuário
    responsável por ele.
    """

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()

        cursor = conexao.cursor(
            dictionary=True
        )

        comando = """
            SELECT
                id AS animal_id,
                responsavel_aplicacao AS usuario_id
            FROM animais
            ORDER BY id ASC
            LIMIT 1
        """

        cursor.execute(
            comando
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


def remover_sessao_teste(
    id_sessao: str,
) -> None:
    """
    Remove a sessão criada no teste.

    Como procedimentos e medicações usam
    ON DELETE CASCADE, os registros associados
    também serão excluídos.
    """

    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()

        cursor = conexao.cursor()

        cursor.execute(
            """
            DELETE FROM sessoes_monitoramento
            WHERE id = %s
            """,
            (id_sessao,),
        )

        conexao.commit()

    finally:
        if cursor is not None:
            cursor.close()

        if (
            conexao is not None
            and conexao.is_connected()
        ):
            conexao.close()


def test_persistencia_procedimento_e_medicacao_mysql():

    dados_animal = buscar_animal_teste()

    if dados_animal is None:
        pytest.skip(
            "Nenhum animal cadastrado "
            "para executar o teste."
        )

    repositorio_sessoes = (
        RepositorioSessoes()
    )

    repositorio_procedimentos = (
        RepositorioProcedimentos()
    )

    repositorio_medicacoes = (
        RepositorioMedicacoes()
    )

    id_sessao = None

    try:
        # -----------------------------------------
        # 1. Criar sessão temporária
        # -----------------------------------------

        id_sessao = (
            repositorio_sessoes
            .iniciar_sessao(
                animal_id=(
                    dados_animal[
                        "animal_id"
                    ]
                ),
                usuario_id=(
                    dados_animal[
                        "usuario_id"
                    ]
                ),
            )
        )

        usuario_id = (
            dados_animal[
                "usuario_id"
            ]
        )

        # -----------------------------------------
        # 2. Salvar procedimento
        # -----------------------------------------

        data_procedimento = datetime(
            2026,
            10,
            18,
            18,
            10,
            0,
        )

        id_procedimento = (
            repositorio_procedimentos
            .salvar(
                sessao_id=id_sessao,
                nome=(
                    "Monitoramento "
                    "anestésico de teste"
                ),
                executado_por=(
                    "Equipe veterinária"
                ),
                registrado_por=(
                    usuario_id
                ),
                data_hora=(
                    data_procedimento
                ),
                observacao=(
                    "Procedimento criado "
                    "pelo teste."
                ),
            )
        )

        # -----------------------------------------
        # 3. Salvar medicação
        # -----------------------------------------

        data_medicacao = datetime(
            2026,
            10,
            18,
            18,
            15,
            0,
        )

        id_medicacao = (
            repositorio_medicacoes
            .salvar(
                sessao_id=id_sessao,
                nome=(
                    "Medicamento de teste"
                ),
                quantidade=2.0,
                unidade="ml",
                administrado_por=(
                    "Equipe veterinária"
                ),
                registrado_por=(
                    usuario_id
                ),
                data_hora=(
                    data_medicacao
                ),
                observacao=(
                    "Medicação criada "
                    "pelo teste."
                ),
            )
        )

        # -----------------------------------------
        # 4. Recuperar registros
        # -----------------------------------------

        procedimentos = (
            repositorio_procedimentos
            .listar_por_sessao(
                id_sessao
            )
        )

        medicacoes = (
            repositorio_medicacoes
            .listar_por_sessao(
                id_sessao
            )
        )

        # -----------------------------------------
        # 5. Validar procedimento
        # -----------------------------------------

        assert len(
            procedimentos
        ) == 1

        procedimento = (
            procedimentos[0]
        )

        assert (
            procedimento["id"]
            == id_procedimento
        )

        assert (
            procedimento["sessao_id"]
            == id_sessao
        )

        assert (
            procedimento["nome"]
            == "Monitoramento anestésico de teste"
        )

        assert (
            procedimento["executado_por"]
            == "Equipe veterinária"
        )

        assert (
            procedimento["registrado_por"]
            == usuario_id
        )

        # -----------------------------------------
        # 6. Validar medicação
        # -----------------------------------------

        assert len(
            medicacoes
        ) == 1

        medicacao = (
            medicacoes[0]
        )

        assert (
            medicacao["id"]
            == id_medicacao
        )

        assert (
            medicacao["sessao_id"]
            == id_sessao
        )

        assert (
            medicacao["nome"]
            == "Medicamento de teste"
        )

        assert (
            medicacao["quantidade"]
            == 2.0
        )

        assert (
            medicacao["unidade"]
            == "ml"
        )

        assert (
            medicacao["administrado_por"]
            == "Equipe veterinária"
        )

        assert (
            medicacao["registrado_por"]
            == usuario_id
        )

        # -----------------------------------------
        # 7. Mostrar resultado
        # -----------------------------------------

        print()
        print(
            "PERSISTÊNCIA CLÍNICA MYSQL"
        )
        print(
            "--------------------------"
        )

        print(
            "Sessão:",
            id_sessao,
        )

        print()
        print(
            "Procedimento:"
        )

        print(
            "ID:",
            procedimento["id"],
        )

        print(
            "Nome:",
            procedimento["nome"],
        )

        print(
            "Executado por:",
            procedimento[
                "executado_por"
            ],
        )

        print()
        print(
            "Medicação:"
        )

        print(
            "ID:",
            medicacao["id"],
        )

        print(
            "Nome:",
            medicacao["nome"],
        )

        print(
            "Quantidade:",
            medicacao["quantidade"],
            medicacao["unidade"],
        )

        print(
            "Administrado por:",
            medicacao[
                "administrado_por"
            ],
        )

    finally:

        # -----------------------------------------
        # 8. Limpeza
        # -----------------------------------------

        if id_sessao is not None:
            remover_sessao_teste(
                id_sessao
            )