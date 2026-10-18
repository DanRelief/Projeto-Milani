from datetime import datetime
from uuid import uuid4

from src.infrastructure.database import get_db_connection

class RepositorioSessoes:

    def iniciar_sessao(self,animal_id: int,usuario_id: int,data_hora_inicio: datetime | None = None,) -> str:

        id_sessao = str(uuid4())

        if data_hora_inicio is None:
            data_hora_inicio = datetime.now()

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            comando = """
                INSERT INTO sessoes_monitoramento (
                    id,
                    animal_id,
                    iniciado_por,
                    data_hora_inicio,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'ativa'
                )
            """

            cursor.execute(comando,(id_sessao,animal_id,usuario_id,data_hora_inicio,),)

            conexao.commit()

            return id_sessao

        except Exception:
            if conexao is not None:
                conexao.rollback()

            raise

        finally:
            if cursor is not None:
                cursor.close()

            if (conexao is not None and conexao.is_connected()):
                conexao.close()
    
    def encerrar_sessao(self,id_sessao: str,data_hora_fim: datetime | None = None,) -> None:

        if data_hora_fim is None:
            data_hora_fim = datetime.now()

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            comando = """
                UPDATE sessoes_monitoramento
                SET
                    data_hora_fim = %s,
                    status = 'encerrada'
                WHERE id = %s
            """

            cursor.execute(comando,(data_hora_fim,id_sessao,),)

            conexao.commit()

        except Exception:
            if conexao is not None:
                conexao.rollback()

            raise

        finally:
            if cursor is not None:
                cursor.close()

            if (conexao is not None and conexao.is_connected()):
                conexao.close()
    
    def buscar_por_id(self,id_sessao: str,) -> dict | None:

        comando = """
            SELECT
                s.id AS sessao_id,
                s.animal_id,
                s.iniciado_por,
                s.data_hora_inicio,
                s.data_hora_fim,
                s.status,

                a.nome AS animal_nome,
                a.especie,
                a.idade,
                a.porte,
                a.estado_clinico,
                a.responsavel_aplicacao,

                responsavel.nome AS nome_responsavel,

                iniciador.nome AS nome_iniciador,
                iniciador.papel AS papel_iniciador

            FROM sessoes_monitoramento s

            INNER JOIN animais a
                ON a.id = s.animal_id

            INNER JOIN usuarios responsavel
                ON responsavel.id =
                a.responsavel_aplicacao

            INNER JOIN usuarios iniciador
                ON iniciador.id =
                s.iniciado_por

            WHERE s.id = %s
        """

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()

            cursor = conexao.cursor(
                dictionary=True
            )

            cursor.execute(
                comando,
                (id_sessao,),
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