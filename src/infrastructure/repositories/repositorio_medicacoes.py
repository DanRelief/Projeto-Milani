from src.infrastructure.database import (
    get_db_connection,
)


class RepositorioMedicacoes:

    def salvar(
        self,
        sessao_id: str,
        nome: str,
        quantidade: float | None,
        unidade: str | None,
        administrado_por: str | None,
        registrado_por: int,
        data_hora,
        observacao: str | None = None,
    ) -> int:

        comando = """
            INSERT INTO medicacoes (
                sessao_id,
                nome,
                quantidade,
                unidade,
                administrado_por,
                registrado_por,
                data_hora,
                observacao
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        valores = (
            sessao_id,
            nome,
            quantidade,
            unidade,
            administrado_por,
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
                    m.id,
                    m.sessao_id,
                    m.nome,
                    m.quantidade,
                    m.unidade,
                    m.administrado_por,
                    m.registrado_por,
                    u.nome AS nome_registrador,
                    m.data_hora,
                    m.observacao

                FROM medicacoes m

                INNER JOIN usuarios u
                    ON u.id = m.registrado_por

                WHERE m.sessao_id = %s

                ORDER BY
                    m.data_hora ASC,
                    m.id ASC
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