import os
import bcrypt
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "1234"),
        database=os.getenv("DB_NAME", "misa"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def autenticar_usuario(role: str, identifier: str, password_plain: str) -> dict | None:
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
        print(f"Erro ao autenticar: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def cadastrar_usuario(
    nome: str, papel: str, identificador: str, senha_plana: str
) -> tuple[bool, str]:
    """Cadastra um novo usuário no banco com senha criptografada."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Criptografa a senha antes de salvar
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(
            senha_plana.encode("utf-8"), salt
        ).decode("utf-8")

        query = """
            INSERT INTO usuarios (nome, papel, identificador, senha_hash)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nome, papel, identificador, senha_hash))
        conn.commit()
        return True, "Usuário cadastrado com sucesso!"
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Código de erro para entrada duplicada (UNIQUE)
            return (
                False,
                "Este RA ou E-mail já está cadastrado no sistema.",
            )
        return False, f"Erro ao acessar o banco de dados: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()