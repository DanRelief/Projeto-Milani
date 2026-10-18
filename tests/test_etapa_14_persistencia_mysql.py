from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.domain.alert import (
    TipoEventoAlerta,
)

from src.domain.measurement import (
    ParametroVital,
)

from src.infrastructure.database import (
    get_db_connection,
)

from src.infrastructure.repositories.repositorio_alertas import (
    RepositorioAlertas,
)

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)


def buscar_animal_teste():
    """
    Busca um animal já cadastrado e o usuário
    responsável por ele.

    Isso evita criar registros artificiais
    de usuário e animal durante o teste.
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
    Remove a sessão criada pelo teste.

    eventos_alerta é removido automaticamente
    devido ao ON DELETE CASCADE.
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


def test_persistencia_real_alerta_mysql():

    dados_animal = buscar_animal_teste()

    if dados_animal is None:
        pytest.skip(
            "Nenhum animal cadastrado "
            "para executar o teste."
        )

    repositorio_sessoes = (
        RepositorioSessoes()
    )

    repositorio_alertas = (
        RepositorioAlertas()
    )

    id_sessao = None

    try:
        # -----------------------------------------
        # 1. Criar sessão real no MySQL
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

        # -----------------------------------------
        # 2. Criar um evento compatível
        #    com RepositorioAlertas
        # -----------------------------------------

        id_alerta = str(
            uuid4()
        )

        data_hora = datetime(
            2026,
            10,
            18,
            18,
            0,
            0,
        )

        evento = SimpleNamespace(
            id_alerta=id_alerta,
            id_sessao=id_sessao,
            tipo_evento=(
                TipoEventoAlerta.ABERTURA
            ),
            parametro=(
                ParametroVital.SPO2
            ),
            data_hora=data_hora,
            estado_monitoramento="alerta",
            valor_atual=95.0,
            z_robusto=-8.5,
            ewma=None,
            inclinacao=None,
            qualidade_sinal=1.0,
            motivo=(
                "Evento criado pelo teste "
                "de integração MySQL."
            ),
        )

        # -----------------------------------------
        # 3. Persistir
        # -----------------------------------------

        repositorio_alertas.salvar(
            evento
        )

        # -----------------------------------------
        # 4. Recuperar
        # -----------------------------------------

        eventos = (
            repositorio_alertas
            .listar_por_sessao(
                id_sessao
            )
        )

        # -----------------------------------------
        # 5. Validar
        # -----------------------------------------

        assert len(eventos) == 1

        evento_salvo = eventos[0]

        assert (
            evento_salvo["id_alerta"]
            == id_alerta
        )

        assert (
            evento_salvo["sessao_id"]
            == id_sessao
        )

        assert (
            evento_salvo["tipo_evento"]
            == "abertura"
        )

        assert (
            evento_salvo["parametro"]
            == "spo2"
        )

        assert (
            evento_salvo[
                "estado_monitoramento"
            ]
            == "alerta"
        )

        assert (
            evento_salvo["valor_atual"]
            == 95.0
        )

        assert (
            evento_salvo["z_robusto"]
            == -8.5
        )

        print()
        print(
            "PERSISTÊNCIA MYSQL"
        )
        print(
            "------------------"
        )

        print(
            "Sessão:",
            id_sessao,
        )

        print(
            "Alerta:",
            evento_salvo[
                "id_alerta"
            ],
        )

        print(
            "Tipo:",
            evento_salvo[
                "tipo_evento"
            ],
        )

        print(
            "Parâmetro:",
            evento_salvo[
                "parametro"
            ],
        )

        print(
            "Valor:",
            evento_salvo[
                "valor_atual"
            ],
        )

        print(
            "Z robusto:",
            evento_salvo[
                "z_robusto"
            ],
        )

    finally:

        # -----------------------------------------
        # 6. Limpeza
        # -----------------------------------------

        if id_sessao is not None:
            remover_sessao_teste(
                id_sessao
            )