from src.infrastructure.database import get_db_connection


class RepositorioAlertas:

    def salvar(self,evento,) -> None:

        comando = """
            INSERT INTO eventos_alerta (
                id_alerta,
                sessao_id,
                tipo_evento,
                parametro,
                data_hora,
                estado_monitoramento,
                valor_atual,
                z_robusto,
                ewma,
                inclinacao,
                qualidade_sinal,
                motivo
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        valores = (
            evento.id_alerta,
            evento.id_sessao,
            evento.tipo_evento.value,
            evento.parametro.value,
            evento.data_hora,
            evento.estado_monitoramento,
            evento.valor_atual,
            evento.z_robusto,
            evento.ewma,
            evento.inclinacao,
            evento.qualidade_sinal,
            evento.motivo,
        )

        conexao = None
        cursor = None

        try:
            conexao = get_db_connection()
            cursor = conexao.cursor()

            cursor.execute(comando,valores,)

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