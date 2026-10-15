import os
import bcrypt
import mysql.connector


def get_db_connection():
    """Conecta ao banco MySQL utilizando variáveis do .env ou valores padrão."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "1234"),
        database=os.getenv("DB_NAME", "misa"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def autenticar_usuario(role: str, identifier: str, password_plain: str) -> dict | None:
    """Valida o login consultando a tabela usuarios no MySQL."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, nome, papel, identificador, senha_hash 
            FROM usuarios 
            WHERE papel = %s AND identificador = %s
        """
        cursor.execute(query, (role, identifier))
        usuario = cursor.fetchone()

        if usuario:
            senha_em_bytes = password_plain.encode("utf-8")
            hash_em_bytes = usuario["senha_hash"].encode("utf-8")

            if bcrypt.checkpw(senha_em_bytes, hash_em_bytes):
                del usuario["senha_hash"]
                return usuario

        return None
    except mysql.connector.Error as err:
        print(f"Erro ao autenticar usuário: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def cadastrar_usuario(nome: str, papel: str, identificador: str, senha_plana: str) -> tuple[bool, str]:
    """Cadastra um novo usuário criptografando a senha em bcrypt."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha_plana.encode("utf-8"), salt).decode("utf-8")

        query = """
            INSERT INTO usuarios (nome, papel, identificador, senha_hash)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nome, papel, identificador, senha_hash))
        conn.commit()
        return True, "Usuário cadastrado com sucesso!"
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return False, "Este RA/E-mail já está cadastrado."
        return False, f"Erro ao acessar o banco de dados: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def cadastrar_animal(dados: dict) -> tuple[bool, str]:
    """Insere um novo animal no MySQL vinculado ao usuário responsável."""
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
            dados["nome"],
            dados["especie"],
            dados["idade"],
            dados["porte"],
            dados["procedimento"],
            dados["estado_clinico"],
            dados.get("ultima_medicacao"),
            dados.get("quantidade"),
            dados["responsavel_aplicacao"]
        ))
        conn.commit()
        return True, "Animal cadastrado com sucesso!"
    except mysql.connector.Error as err:
        return False, f"Erro ao salvar animal: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def listar_animais() -> list[dict]:
    """Retorna todos os animais cadastrados com o nome do usuário responsável."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                a.id, a.nome, a.especie, a.idade, a.porte, a.procedimento,
                a.estado_clinico, a.ultima_medicacao, a.quantidade,
                a.responsavel_aplicacao, u.nome AS nome_responsavel
            FROM animais a
            INNER JOIN usuarios u ON a.responsavel_aplicacao = u.id
            ORDER BY a.id DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar animais: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()