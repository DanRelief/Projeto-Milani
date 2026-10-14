import os
import bcrypt
import mysql.connector

# Dados de conexão ao banco MySQL
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "1234"), # Coloque a senha do seu MySQL aqui se não usar .env
    database=os.getenv("DB_NAME", "misa"),
    port=int(os.getenv("DB_PORT", "3306")),
)

cursor = conn.cursor()

# Dados do usuário de teste
nome = "Bryan Martini"
papel = "student"         # 'student' para Aluno ou 'teacher' para Docente
identificador = "1115152"  # RA se for aluno ou e-mail se for docente
senha_plana = "1234"      # Senha em texto puro

# Criptografia com bcrypt
salt = bcrypt.gensalt()
senha_hash = bcrypt.hashpw(senha_plana.encode("utf-8"), salt).decode("utf-8")

# Inserção no banco
query = """
    INSERT INTO usuarios (nome, papel, identificador, senha_hash)
    VALUES (%s, %s, %s, %s)
"""

try:
    cursor.execute(query, (nome, papel, identificador, senha_hash))
    conn.commit()
    print(" Usuário de teste cadastrado com sucesso!")
except mysql.connector.Error as err:
    print(f" Erro ao cadastrar usuário: {err}")
finally:
    cursor.close()
    conn.close()