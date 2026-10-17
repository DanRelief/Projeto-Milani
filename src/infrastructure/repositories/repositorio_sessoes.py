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