from src.infrastructure.database import get_db_connection


class RepositorioMedicoes:

    def salvar_lote(self,medicoes) -> None:

        if not medicoes:
            return

        comando = """
            INSERT INTO medicoes_sinais_vitais (
                sessao_id,
                data_hora,
                parametro,
                valor,
                unidade,
                fonte,
                qualidade_sinal,
                valida
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        valores = [
            (
                medicao.id_sessao,
                medicao.data_hora,
                medicao.parametro.value,
                medicao.valor,
                medicao.unidade,
                medicao.fonte.value,
                medicao.qualidade_sinal,
                medicao.valida,
            )
            for medicao in medicoes
        ]

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            cursor.executemany(comando,valores,)

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

    def listar_por_sessao(self,id_sessao: str,) -> list[dict]:

        comando = """
            SELECT
                id,
                sessao_id,
                data_hora,
                parametro,
                valor,
                unidade,
                fonte,
                qualidade_sinal,
                valida
            FROM medicoes_sinais_vitais
            WHERE
                sessao_id = %s
                AND valida = TRUE
            ORDER BY
                data_hora ASC,
                id ASC
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