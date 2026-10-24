import os
import uuid
from datetime import datetime
from pathlib import Path

import bcrypt
import mysql.connector
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _obter_variavel_obrigatoria(nome: str) -> str:
    """Retorna uma variável obrigatória do .env ou interrompe com erro claro."""
    valor = os.getenv(nome)

    if valor is None or valor.strip() == "":
        raise RuntimeError(
            f"Variável de ambiente obrigatória não definida: {nome}"
        )

    return valor


def get_db_connection():
    """Conecta ao MySQL exclusivamente com as configurações definidas no .env."""
    return mysql.connector.connect(
        host=_obter_variavel_obrigatoria("DB_HOST"),
        user=_obter_variavel_obrigatoria("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        database=_obter_variavel_obrigatoria("DB_NAME"),
        port=int(_obter_variavel_obrigatoria("DB_PORT")),
    )

# --- USUÁRIOS E AUTENTICAÇÃO ---

def _fechar_conexao(conexao, cursor) -> None:
    """Fecha cursor e conexão com segurança."""
    if cursor is not None:
        cursor.close()

    if conexao is not None and conexao.is_connected():
        conexao.close()


# ============================================================================
# USUÁRIOS E AUTENTICAÇÃO
# ============================================================================


def autenticar_usuario(
    role: str,
    identifier: str,
    password_plain: str,
) -> dict | None:
    """Valida login e retorna os dados públicos do usuário."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        query = """
            SELECT
                id,
                nome,
                papel,
                identificador,
                senha_hash,
                primeiro_acesso
            FROM usuarios
            WHERE papel = %s
              AND identificador = %s
        """

        cursor.execute(query, (role, identifier))
        usuario = cursor.fetchone()

        if usuario is None:
            return None

        senha_correta = bcrypt.checkpw(
            password_plain.encode("utf-8"),
            usuario["senha_hash"].encode("utf-8"),
        )

        if not senha_correta:
            return None

        del usuario["senha_hash"]
        return usuario

    except mysql.connector.Error as erro:
        print(f"Erro ao autenticar usuário: {erro}")
        return None

    finally:
        _fechar_conexao(conexao, cursor)


def cadastrar_usuario(
    nome: str,
    papel: str,
    identificador: str,
    senha_plana: str,
) -> tuple[bool, str]:
    """Cadastra um usuário armazenando a senha com bcrypt."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(
            senha_plana.encode("utf-8"),
            salt,
        ).decode("utf-8")

        query = """
            INSERT INTO usuarios (
                nome,
                papel,
                identificador,
                senha_hash
            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (nome, papel, identificador, senha_hash),
        )
        conexao.commit()

        return True, "Usuário cadastrado com sucesso!"

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        if erro.errno == 1062:
            return False, "Este RA/E-mail já está cadastrado."

        return False, f"Erro ao acessar o banco de dados: {erro}"

    finally:
        _fechar_conexao(conexao, cursor)


def listar_alunos() -> list[dict]:
    """Retorna os alunos disponíveis para atribuição de animais."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        query = """
            SELECT
                id,
                nome,
                identificador
            FROM usuarios
            WHERE papel = 'student'
            ORDER BY nome
        """

        cursor.execute(query)
        return cursor.fetchall()

    except mysql.connector.Error as erro:
        print(f"Erro ao listar alunos: {erro}")
        return []

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# ANIMAIS
# ============================================================================


def cadastrar_animal(dados: dict) -> tuple[bool, str]:
    """Insere um animal e o vincula ao usuário responsável."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query = """
            INSERT INTO animais (
                nome,
                especie,
                idade,
                porte,
                procedimento,
                estado_clinico,
                ultima_medicacao,
                quantidade,
                responsavel_aplicacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                dados["nome"],
                dados["especie"],
                dados["idade"],
                dados["porte"],
                dados["procedimento"],
                dados["estado_clinico"],
                dados.get("ultima_medicacao"),
                dados.get("quantidade"),
                dados["responsavel_aplicacao"],
            ),
        )

        conexao.commit()
        return True, "Animal cadastrado com sucesso!"

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        return False, f"Erro ao cadastrar animal: {erro}"

    finally:
        _fechar_conexao(conexao, cursor)


def listar_animais() -> list[dict]:
    """Retorna todos os animais com os dados do usuário responsável."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        query = """
            SELECT
                a.id,
                a.nome,
                a.especie,
                a.idade,
                a.porte,
                a.procedimento,
                a.estado_clinico,
                a.ultima_medicacao,
                a.quantidade,
                a.observacao_docente,
                a.responsavel_aplicacao,
                u.nome AS nome_responsavel,
                u.identificador AS identificador_responsavel
            FROM animais a
            INNER JOIN usuarios u
                ON a.responsavel_aplicacao = u.id
            ORDER BY a.id DESC
        """

        cursor.execute(query)
        return cursor.fetchall()

    except mysql.connector.Error as erro:
        print(f"Erro ao buscar animais: {erro}")
        return []

    finally:
        _fechar_conexao(conexao, cursor)


def atribuir_animal_aluno(
    animal_id: int,
    aluno_id: int,
) -> bool:
    """Altera o aluno responsável por um animal."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        # Garante que o usuário escolhido realmente seja um aluno.
        cursor.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = %s
              AND papel = 'student'
            """,
            (aluno_id,),
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            UPDATE animais
            SET responsavel_aplicacao = %s
            WHERE id = %s
            """,
            (aluno_id, animal_id),
        )

        conexao.commit()
        return cursor.rowcount > 0

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao atribuir animal ao aluno: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


def salvar_observacao_docente(
    animal_id: int,
    observacao: str,
) -> bool:
    """Salva a observação do docente no cadastro permanente do animal."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query = """
            UPDATE animais
            SET observacao_docente = %s
            WHERE id = %s
        """

        cursor.execute(query, (observacao, animal_id))
        conexao.commit()

        return cursor.rowcount > 0

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao salvar observação do docente: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# COMPATIBILIDADE COM A INTERFACE ANTIGA
#
# O fluxo novo do M.I.S.A. usa RepositorioSessoes e RepositorioMedicoes.
# Estas funções permanecem apenas para não quebrar telas antigas do projeto.
# Não chame as duas abordagens ao mesmo tempo, pois isso duplicará dados.
# ============================================================================


def criar_sessao_monitoramento(
    animal_id: int,
    iniciado_por: int,
) -> str | None:
    """Cria uma sessão diretamente no banco para compatibilidade legada."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        sessao_id = str(uuid.uuid4())
        agora = datetime.now()

        query = """
            INSERT INTO sessoes_monitoramento (
                id,
                animal_id,
                iniciado_por,
                data_hora_inicio,
                status
            )
            VALUES (%s, %s, %s, %s, 'ativa')
        """

        cursor.execute(
            query,
            (sessao_id, animal_id, iniciado_por, agora),
        )
        conexao.commit()

        return sessao_id

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao criar sessão: {erro}")
        return None

    finally:
        _fechar_conexao(conexao, cursor)


def salvar_medicao_sinal_vital(
    sessao_id: str,
    parametro: str,
    valor: float,
    unidade: str,
    fonte: str = "simulador",
    qualidade_sinal: float | None = None,
    valida: bool = True,
) -> bool:
    """Salva uma medição diretamente no banco para compatibilidade legada."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query = """
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                sessao_id,
                datetime.now(),
                parametro,
                valor,
                unidade,
                fonte,
                qualidade_sinal,
                valida,
            ),
        )
        conexao.commit()

        return True

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao salvar medição: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# HISTÓRICO PERMANENTE DE PROCEDIMENTOS
# ============================================================================


def salvar_historico_procedimento(
    animal_id: int,
    realizado_por: int,
    procedimento: str,
    descricao_detalhada: str | None = None,
    sessao_id: str | None = None,
    registrado_por: int | None = None,
    data_hora: datetime | None = None,
) -> bool:
    """Registra permanentemente um procedimento do animal.

    ``sessao_id`` é opcional para permitir registros históricos fora de uma
    sessão de monitoramento.
    """
    conexao = None
    cursor = None

    if registrado_por is None:
        registrado_por = realizado_por

    if data_hora is None:
        data_hora = datetime.now()

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query = """
            INSERT INTO historico_procedimentos (
                animal_id,
                sessao_id,
                realizado_por,
                registrado_por,
                procedimento,
                descricao_detalhada,
                data_hora
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                animal_id,
                sessao_id,
                realizado_por,
                registrado_por,
                procedimento,
                descricao_detalhada,
                data_hora,
            ),
        )

        # Mantém o resumo do último procedimento na tabela animais.
        cursor.execute(
            """
            UPDATE animais
            SET procedimento = %s
            WHERE id = %s
            """,
            (procedimento, animal_id),
        )

        conexao.commit()
        return True

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao salvar procedimento: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# HISTÓRICO PERMANENTE DE MEDICAÇÕES
# ============================================================================


def salvar_historico_medicacao(
    animal_id: int,
    administrado_por: int,
    medicamento: str,
    dose_quantidade: str,
    via_administracao: str | None = None,
    observacao: str | None = None,
    sessao_id: str | None = None,
    registrado_por: int | None = None,
    quantidade: float | None = None,
    unidade: str | None = None,
    data_hora: datetime | None = None,
) -> bool:
    """Registra permanentemente uma medicação administrada ao animal."""
    conexao = None
    cursor = None

    if registrado_por is None:
        registrado_por = administrado_por

    if data_hora is None:
        data_hora = datetime.now()

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        query = """
            INSERT INTO historico_medicacoes (
                animal_id,
                sessao_id,
                administrado_por,
                registrado_por,
                medicamento,
                quantidade,
                unidade,
                dose_quantidade,
                via_administracao,
                observacao,
                data_hora
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                animal_id,
                sessao_id,
                administrado_por,
                registrado_por,
                medicamento,
                quantidade,
                unidade,
                dose_quantidade,
                via_administracao,
                observacao,
                data_hora,
            ),
        )

        # Mantém o resumo da última medicação na tabela animais para a UI.
        cursor.execute(
            """
            UPDATE animais
            SET
                ultima_medicacao = %s,
                quantidade = %s
            WHERE id = %s
            """,
            (medicamento, dose_quantidade, animal_id),
        )

        conexao.commit()
        return True

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao salvar medicação: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# CONSULTA DO HISTÓRICO COMPLETO DO ANIMAL
# ============================================================================


def carregar_historico_animal(animal_id: int) -> list[dict]:
    """Retorna procedimentos e medicações permanentes em uma única linha do tempo."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor(dictionary=True)

        query_procedimentos = """
            SELECT
                hp.id,
                'Procedimento' AS tipo,
                hp.animal_id,
                hp.sessao_id,
                hp.procedimento,
                hp.descricao_detalhada,
                realizador.nome AS medico_procedimento,
                registrador.nome AS registrado_por_nome,
                DATE_FORMAT(hp.data_hora, '%d/%m/%Y') AS data,
                DATE_FORMAT(hp.data_hora, '%H:%i') AS hora,
                hp.data_hora
            FROM historico_procedimentos hp
            INNER JOIN usuarios realizador
                ON hp.realizado_por = realizador.id
            INNER JOIN usuarios registrador
                ON hp.registrado_por = registrador.id
            WHERE hp.animal_id = %s
        """

        cursor.execute(query_procedimentos, (animal_id,))
        procedimentos = cursor.fetchall()

        query_medicacoes = """
            SELECT
                hm.id,
                'Medicação' AS tipo,
                hm.animal_id,
                hm.sessao_id,
                hm.medicamento AS medicacao,
                hm.quantidade AS quantidade_valor,
                hm.unidade,
                hm.dose_quantidade AS quantidade,
                hm.via_administracao,
                hm.observacao,
                administrador.nome AS medico_medicacao,
                registrador.nome AS registrado_por_nome,
                DATE_FORMAT(hm.data_hora, '%d/%m/%Y') AS data,
                DATE_FORMAT(hm.data_hora, '%H:%i') AS hora,
                hm.data_hora
            FROM historico_medicacoes hm
            INNER JOIN usuarios administrador
                ON hm.administrado_por = administrador.id
            INNER JOIN usuarios registrador
                ON hm.registrado_por = registrador.id
            WHERE hm.animal_id = %s
        """

        cursor.execute(query_medicacoes, (animal_id,))
        medicacoes = cursor.fetchall()

        historico = procedimentos + medicacoes
        historico.sort(
            key=lambda item: item.get("data_hora") or datetime.min,
            reverse=True,
        )

        return historico

    except mysql.connector.Error as erro:
        print(f"Erro ao carregar histórico do animal: {erro}")
        return []

    finally:
        _fechar_conexao(conexao, cursor)


# ============================================================================
# EXCLUSÃO DO HISTÓRICO
# ============================================================================


def deletar_historico_procedimento(procedimento_id: int) -> bool:
    """Remove um procedimento permanente pelo ID."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(
            "DELETE FROM historico_procedimentos WHERE id = %s",
            (procedimento_id,),
        )

        conexao.commit()
        return cursor.rowcount > 0

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao deletar procedimento: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)


def deletar_historico_medicacao(medicacao_id: int) -> bool:
    """Remove uma medicação permanente pelo ID."""
    conexao = None
    cursor = None

    try:
        conexao = get_db_connection()
        cursor = conexao.cursor()

        cursor.execute(
            "DELETE FROM historico_medicacoes WHERE id = %s",
            (medicacao_id,),
        )

        conexao.commit()
        return cursor.rowcount > 0

    except mysql.connector.Error as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro ao deletar medicação: {erro}")
        return False

    finally:
        _fechar_conexao(conexao, cursor)
