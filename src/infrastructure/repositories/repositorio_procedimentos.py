from src.infrastructure.database import (
    get_db_connection,
)


class RepositorioProcedimentos:

    def salvar(
        self,
        sessao_id: str,
        nome: str,
        executado_por: str | None,
        registrado_por: int,
        data_hora,
        observacao: str | None = None,
    ) -> int:

        comando = """
            INSERT INTO procedimentos (
                sessao_id,
                nome,
                executado_por,
                registrado_por,
                data_hora,
                observacao
            )
            VALUES (
                %s, %s, %s,
                %s, %s, %s
            )
        """

        valores = (
            sessao_id,
            nome,
            executado_por,
            registrado_por,
            data_hora,
            observacao,
        )

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()

            cursor = conexao.cursor()

            cursor.execute(
                comando,
                valores,
            )

            conexao.commit()

            return cursor.lastrowid

        except Exception:
            if conexao is not None:
                conexao.rollback()

            raise

        finally:
            if cursor is not None:
                cursor.close()

            if (
                conexao is not None
                and conexao.is_connected()
            ):
                conexao.close()

    def listar_por_sessao(
        self,
        id_sessao: str,
    ) -> list[dict]:

        comando = """
                SELECT
                    p.id,
                    p.sessao_id,
                    p.nome,
                    p.executado_por,
                    p.registrado_por,
                    u.nome AS nome_registrador,
                    p.data_hora,
                    p.observacao

                FROM procedimentos p

                INNER JOIN usuarios u
                    ON u.id = p.registrado_por

                WHERE p.sessao_id = %s

                ORDER BY
                    p.data_hora ASC,
                    p.id ASC
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

            return cursor.fetchall()

        finally:
            if cursor is not None:
                cursor.close()

            if (
                conexao is not None
                and conexao.is_connected()
            ):
                conexao.close()