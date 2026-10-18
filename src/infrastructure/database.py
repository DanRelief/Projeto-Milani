import os
import uuid
import bcrypt
import mysql.connector
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "1234"),
        database=os.getenv("DB_NAME", "misa"),
        port=int(os.getenv("DB_PORT", "3306")),
    )

# --- USUÁRIOS E AUTENTICAÇÃO ---

def autenticar_usuario(role: str, identifier: str, password_plain: str) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, nome, papel, identificador, senha_hash, primeiro_acesso 
            FROM usuarios 
            WHERE papel = %s AND identificador = %s
        """
        cursor.execute(query, (role, identifier))
        usuario = cursor.fetchone()

        if usuario and bcrypt.checkpw(password_plain.encode("utf-8"), usuario["senha_hash"].encode("utf-8")):
            del usuario["senha_hash"]
            return usuario
        return None
    except mysql.connector.Error as err:
        print(f"Erro no MySQL: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def cadastrar_usuario(nome: str, papel: str, identificador: str, senha_plana: str) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha_plana.encode("utf-8"), salt).decode("utf-8")

        query = "INSERT INTO usuarios (nome, papel, identificador, senha_hash) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nome, papel, identificador, senha_hash))
        conn.commit()
        return True, "Usuário cadastrado com sucesso!"
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return False, "Este RA/E-mail já está cadastrado."
        return False, f"Erro ao acessar banco: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def cadastrar_animal(dados: dict) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO animais (
                nome, especie, idade, porte, procedimento, 
                estado_clinico, ultima_medicacao, quantidade, responsavel_aplicacao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            dados["nome"], dados["especie"], dados["idade"], dados["porte"],
            dados["procedimento"], dados["estado_clinico"],
            dados.get("ultima_medicacao"), dados.get("quantidade"),
            dados["responsavel_aplicacao"]
        ))
        conn.commit()
        return True, "Animal cadastrado com sucesso!"
    except mysql.connector.Error as err:
        return False, f"Erro ao cadastrar animal: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def listar_animais() -> list[dict]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id, a.nome, a.especie, a.idade, a.porte, a.procedimento,
                a.estado_clinico, a.ultima_medicacao, a.quantidade,
                a.observacao_docente, a.responsavel_aplicacao, 
                u.nome AS nome_responsavel
            FROM animais a
            INNER JOIN usuarios u ON a.responsavel_aplicacao = u.id
            ORDER BY a.id DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar lista de animais: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def criar_sessao_monitoramento(animal_id: int, iniciado_por: int) -> str | None:
    """Abre uma nova sessão ativa de monitoramento com ID UUID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sessao_id = str(uuid.uuid4())
        agora = datetime.now()

        query = """
            INSERT INTO sessoes_monitoramento (id, animal_id, iniciado_por, data_hora_inicio, status)
            VALUES (%s, %s, %s, %s, 'ativa')
        """
        cursor.execute(query, (sessao_id, animal_id, iniciado_por, agora))
        conn.commit()
        return sessao_id
    except mysql.connector.Error as err:
        print(f"Erro ao criar sessão: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def salvar_observacao_docente(animal_id: int, observacao: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE animais SET observacao_docente = %s WHERE id = %s"
        cursor.execute(query, (observacao, animal_id))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar observação: {err}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def salvar_medicao_sinal_vital(sessao_id: str, parametro: str, valor: float, unidade: str, fonte: str = "simulador") -> bool:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO medicoes_sinais_vitais (sessao_id, data_hora, parametro, valor, unidade, fonte)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (sessao_id, datetime.now(), parametro, valor, unidade, fonte))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar medição: {err}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def salvar_historico_procedimento(
    animal_id: int, realizado_por: int, procedimento: str
) -> bool:
    """Insere um novo procedimento no banco de dados."""
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        query = """
            INSERT INTO historico_procedimentos (animal_id, realizado_por, procedimento, data_hora)
            VALUES (%s, %s, %s, NOW());
        """
        cursor.execute(query, (animal_id, realizado_por, procedimento))

        # Atualiza o último procedimento registrado na tabela de animais
        query_update = "UPDATE animais SET procedimento = %s WHERE id = %s;"
        cursor.execute(query_update, (procedimento, animal_id))

        conexao.commit()
        cursor.close()
        conexao.close()
        return True
    except Exception as err:
        print(f"Erro ao salvar procedimento: {err}")
        return False


def salvar_historico_medicacao(
    animal_id: int,
    administrado_por: int,
    medicamento: str,
    dose_quantidade: str,
) -> bool:
    """Insere uma nova medicação no banco de dados."""
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()
        query = """
            INSERT INTO historico_medicacoes (animal_id, administrado_por, medicamento, dose_quantidade, data_hora)
            VALUES (%s, %s, %s, %s, NOW());
        """
        cursor.execute(
            query, (animal_id, administrado_por, medicamento, dose_quantidade)
        )

        # Atualiza a última medicação e dose na tabela de animais
        query_update = """
            UPDATE animais 
            SET ultima_medicacao = %s, quantidade = %s 
            WHERE id = %s;
        """
        cursor.execute(query_update, (medicamento, dose_quantidade, animal_id))

        conexao.commit()
        cursor.close()
        conexao.close()
        return True
    except Exception as err:
        print(f"Erro ao salvar medicação: {err}")
        return False


def carregar_historico_animal(animal_id: int) -> list[dict]:
    """Busca o histórico unificado de procedimentos e medicações do animal no banco."""
    historico_unificado = []
    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        # 1. Busca procedimentos
        query_proc = """
            SELECT 
                'Procedimento' AS tipo,
                hp.procedimento AS procedimento,
                u.nome AS medico_procedimento,
                DATE_FORMAT(hp.data_hora, '%d/%m/%Y') AS data,
                DATE_FORMAT(hp.data_hora, '%H:%i') AS hora,
                hp.data_hora
            FROM historico_procedimentos hp
            INNER JOIN usuarios u ON hp.realizado_por = u.id
            WHERE hp.animal_id = %s
        """
        cursor.execute(query_proc, (animal_id,))
        procedimentos = cursor.fetchall()

        # 2. Busca medicações
        query_med = """
            SELECT 
                'Medicação' AS tipo,
                hm.medicamento AS medicacao,
                hm.dose_quantidade AS quantidade,
                '' AS unidade,
                u.nome AS medico_medicacao,
                DATE_FORMAT(hm.data_hora, '%d/%m/%Y') AS data,
                DATE_FORMAT(hm.data_hora, '%H:%i') AS hora,
                hm.data_hora
            FROM historico_medicacoes hm
            INNER JOIN usuarios u ON hm.administrado_por = u.id
            WHERE hm.animal_id = %s
        """
        cursor.execute(query_med, (animal_id,))
        medicacoes = cursor.fetchall()

        # Unifica e ordena do mais recente para o mais antigo
        historico_unificado = procedimentos + medicacoes
        historico_unificado.sort(
            key=lambda x: x.get("data_hora"), reverse=True
        )

        cursor.close()
        conexao.close()
    except Exception as err:
        print(f"Erro ao carregar histórico do banco: {err}")

    return historico_unificado