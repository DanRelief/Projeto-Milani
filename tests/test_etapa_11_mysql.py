from src.infrastructure.database import get_db_connection
from datetime import datetime

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)

from src.infrastructure.repositories.repositorio_medicoes import (
    RepositorioMedicoes,
)

from src.infrastructure.simulation.sinais_vitais_simulacao import (
    SimuladorSinaisVitais,
)
from datetime import datetime
from uuid import uuid4

from src.domain.alert import (
    EventoAlerta,
    TipoEventoAlerta,
)

from src.domain.measurement import (
    ParametroVital,
)

from src.infrastructure.repositories.repositorio_alertas import (
    RepositorioAlertas,
)

from src.infrastructure.repositories.repositorio_sessoes import (
    RepositorioSessoes,
)
def test_conexao_mysql():

    conexao = get_db_connection()

    assert conexao.is_connected()

    cursor = conexao.cursor()

    cursor.execute(
        "SELECT DATABASE();"
    )

    banco = cursor.fetchone()[0]

    print()
    print(
        "Banco conectado:",
        banco
    )

    assert banco == "misa"

    cursor.close()
    conexao.close()

def test_salvar_sessao_e_medicoes():

    conexao = get_db_connection()
    cursor = conexao.cursor(dictionary=True)

    # Pega um animal já cadastrado e seu responsável.
    cursor.execute(
        """
        SELECT
            id,
            responsavel_aplicacao
        FROM animais
        ORDER BY id
        LIMIT 1
        """
    )

    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    assert animal is not None, (
        "É necessário ter pelo menos "
        "um animal cadastrado para este teste."
    )

    id_animal = animal["id"]
    id_usuario = animal["responsavel_aplicacao"]

    repositorio_sessoes = RepositorioSessoes()
    repositorio_medicoes = RepositorioMedicoes()

    id_sessao = (
        repositorio_sessoes.iniciar_sessao(
            animal_id=id_animal,
            usuario_id=id_usuario,
            data_hora_inicio=datetime(
                2026,
                10,
                16,
                10,
                0,
                0,
            ),
        )
    )

    print()
    print(
        "Sessão criada:",
        id_sessao
    )

    simulador = SimuladorSinaisVitais(
        id_paciente=str(id_animal),
        id_sessao=id_sessao,
        seed=42,
    )

    medicoes = simulador.generate_series(
        duration_minutes=10,
        interval_seconds=5,
        start_time=datetime(
            2026,
            10,
            16,
            10,
            0,
            0,
        ),
    )

    print(
        "Medições geradas:",
        len(medicoes)
    )

    assert len(medicoes) == 360

    repositorio_medicoes.salvar_lote(
        medicoes
    )

    conexao = get_db_connection()
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM medicoes_sinais_vitais
        WHERE sessao_id = %s
        """,
        (id_sessao,),
    )

    quantidade_salva = cursor.fetchone()[0]

    print(
        "Medições encontradas no banco:",
        quantidade_salva
    )

    assert quantidade_salva == 360

    cursor.close()
    conexao.close()

def test_salvar_evento_alerta():

    # --------------------------------
    # Busca um animal existente
    # --------------------------------

    conexao = get_db_connection()
    cursor = conexao.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            id,
            responsavel_aplicacao
        FROM animais
        ORDER BY id
        LIMIT 1
        """
    )

    animal = cursor.fetchone()

    cursor.close()
    conexao.close()

    assert animal is not None

    # --------------------------------
    # Cria uma sessão para o teste
    # --------------------------------

    repositorio_sessoes = (
        RepositorioSessoes()
    )

    id_sessao = (
        repositorio_sessoes
        .iniciar_sessao(
            animal_id=animal["id"],
            usuario_id=(
                animal[
                    "responsavel_aplicacao"
                ]
            ),
            data_hora_inicio=datetime(
                2026,
                10,
                16,
                10,
                0,
                0,
            ),
        )
    )

    # --------------------------------
    # Simula um evento produzido
    # pelo Motor de Alertas
    # --------------------------------

    id_alerta = str(
        uuid4()
    )

    evento = EventoAlerta(
        id_alerta=id_alerta,

        tipo_evento=(
            TipoEventoAlerta.ABERTURA
        ),

        id_paciente=str(
            animal["id"]
        ),

        id_sessao=id_sessao,

        parametro=(
            ParametroVital.SPO2
        ),

        data_hora=datetime(
            2026,
            10,
            16,
            10,
            6,
            15,
        ),

        estado_monitoramento="alerta",

        valor_atual=96.56,

        z_robusto=-5.50,

        ewma=97.10,

        inclinacao=-0.75,

        qualidade_sinal=0.95,

        motivo=(
            "Alteração persistente "
            "detectada na SpO2."
        ),
    )

    # --------------------------------
    # Persiste
    # --------------------------------

    repositorio_alertas = (
        RepositorioAlertas()
    )

    repositorio_alertas.salvar(
        evento
    )

    # --------------------------------
    # Confere no banco
    # --------------------------------

    conexao = get_db_connection()
    cursor = conexao.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *
        FROM eventos_alerta
        WHERE id_alerta = %s
        """,
        (id_alerta,),
    )

    registro = cursor.fetchone()

    print()
    print("EVENTO SALVO")
    print("----------------")

    print(
        "ID alerta:",
        registro["id_alerta"]
    )

    print(
        "Tipo:",
        registro["tipo_evento"]
    )

    print(
        "Parâmetro:",
        registro["parametro"]
    )

    print(
        "Valor:",
        registro["valor_atual"]
    )

    print(
        "Z robusto:",
        registro["z_robusto"]
    )

    cursor.close()
    conexao.close()

    assert registro is not None

    assert (
        registro["tipo_evento"]
        == "abertura"
    )

    assert (
        registro["parametro"]
        == "spo2"
    )