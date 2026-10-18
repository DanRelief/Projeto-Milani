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