from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.infrastructure.database import (
    cadastrar_animal,
    listar_alunos,
)


class DialogCadastrarAnimal(QDialog):

    def __init__(
        self,
        usuario_logado: dict,
        parent=None,
    ):
        super().__init__(parent)

        self.usuario_logado = usuario_logado

        self.setWindowTitle(
            "Cadastrar Novo Animal - M.I.S.A. (Docente)"
        )
        self.setMinimumSize(420, 480)

        layout = QVBoxLayout()

        titulo = QLabel("Cadastro de Paciente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "font-size: 16px; "
            "font-weight: bold; "
            "color: #1f4d3a;"
        )

        layout.addWidget(titulo)

        formulario = QFormLayout()

        # -----------------------------------------
        # ALUNO RESPONSÁVEL
        # -----------------------------------------

        self.combo_aluno = QComboBox()
        self.combo_aluno.setView(QListView())

        self._carregar_alunos()

        # -----------------------------------------
        # DADOS DO ANIMAL
        # -----------------------------------------

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText(
            "Ex: Rex, Thor..."
        )

        self.input_especie = QLineEdit()
        self.input_especie.setPlaceholderText(
            "Ex: Canina, Felina, Equina..."
        )

        self.input_idade = QSpinBox()
        self.input_idade.setRange(0, 100)

        self.combo_porte = QComboBox()
        self.combo_porte.setView(QListView())

        self.combo_porte.addItem(
            "Pequeno",
            "pequeno",
        )

        self.combo_porte.addItem(
            "Médio",
            "medio",
        )

        self.combo_porte.addItem(
            "Grande",
            "grande",
        )

        self.input_procedimento = QLineEdit()
        self.input_procedimento.setPlaceholderText(
            "Ex: Pós-operatório, Monitoramento..."
        )

        self.combo_estado = QComboBox()
        self.combo_estado.setView(QListView())

        self.combo_estado.addItem(
            "Estável",
            "estavel",
        )

        self.combo_estado.addItem(
            "Moderado",
            "moderado",
        )

        self.combo_estado.addItem(
            "Grave",
            "grave",
        )

        self.input_medicacao = QLineEdit()
        self.input_medicacao.setPlaceholderText(
            "Ex: Dipirona, Propofol..."
        )

        self.input_quantidade = QLineEdit()
        self.input_quantidade.setPlaceholderText(
            "Ex: 2ml, 1 comprimido..."
        )

        # -----------------------------------------
        # FORMULÁRIO
        # -----------------------------------------

        formulario.addRow(
            "Aluno Responsável:",
            self.combo_aluno,
        )

        formulario.addRow(
            "Nome do Animal:",
            self.input_nome,
        )

        formulario.addRow(
            "Espécie:",
            self.input_especie,
        )

        formulario.addRow(
            "Idade (anos):",
            self.input_idade,
        )

        formulario.addRow(
            "Porte:",
            self.combo_porte,
        )

        formulario.addRow(
            "Procedimento Inicial:",
            self.input_procedimento,
        )

        formulario.addRow(
            "Estado Clínico:",
            self.combo_estado,
        )

        formulario.addRow(
            "Última Medicação:",
            self.input_medicacao,
        )

        formulario.addRow(
            "Dose/Quantidade:",
            self.input_quantidade,
        )

        layout.addLayout(formulario)

        botao_salvar = QPushButton(
            "Salvar Cadastro"
        )

        botao_salvar.clicked.connect(
            self._salvar
        )

        layout.addWidget(botao_salvar)

        self.setLayout(layout)

        self._aplicar_estilo()

    def _carregar_alunos(self) -> None:
        """Carrega alunos cadastrados no banco."""

        alunos = listar_alunos()

        if not alunos:
            self.combo_aluno.addItem(
                "Nenhum aluno cadastrado no sistema",
                None,
            )
            return

        for aluno in alunos:
            self.combo_aluno.addItem(
                (
                    f"{aluno['nome']} "
                    f"(RA: {aluno['identificador']})"
                ),
                aluno["id"],
            )

    def _salvar(self) -> None:

        nome = self.input_nome.text().strip()
        especie = self.input_especie.text().strip()
        procedimento = (
            self.input_procedimento
            .text()
            .strip()
        )

        aluno_id = (
            self.combo_aluno.currentData()
        )

        if (
            not nome
            or not especie
            or not procedimento
        ):
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Preencha os campos obrigatórios: "
                    "Nome do Animal, Espécie e "
                    "Procedimento."
                ),
            )
            return

        if aluno_id is None:
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Selecione um Aluno Responsável "
                    "válido para cadastrar o animal."
                ),
            )
            return

        dados = {
            "nome": nome,
            "especie": especie,
            "idade": self.input_idade.value(),
            "porte": (
                self.combo_porte.currentData()
            ),
            "procedimento": procedimento,
            "estado_clinico": (
                self.combo_estado.currentData()
            ),
            "ultima_medicacao": (
                self.input_medicacao.text().strip()
                or None
            ),
            "quantidade": (
                self.input_quantidade.text().strip()
                or None
            ),

            # ID do aluno escolhido pelo docente
            "responsavel_aplicacao": aluno_id,
        }

        sucesso, mensagem = cadastrar_animal(
            dados
        )

        if sucesso:
            QMessageBox.information(
                self,
                "Sucesso",
                mensagem,
            )

            self.accept()

        else:
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                mensagem,
            )

    def _aplicar_estilo(self) -> None:

        self.setStyleSheet(
            """
            QDialog {
                background-color: #f7f9fc;
            }

            QLabel {
                color: #2c3e50;
                font-size: 13px;
                font-weight: 500;
            }

            QLineEdit,
            QComboBox,
            QSpinBox {
                min-height: 28px;
                padding: 2px 8px;
                border: 1px solid #c7d0d9;
                border-radius: 5px;
                background: white;
                color: #1a1a1a;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus {
                border: 1px solid #287a55;
            }

            QComboBox QAbstractItemView {
                border: 1px solid #c7d0d9;
                background-color: #ffffff;
                color: #1a1a1a;
                selection-background-color: #287a55;
                selection-color: #ffffff;
                padding: 4px;
            }

            QPushButton {
                min-height: 36px;
                color: white;
                background-color: #287a55;
                border: none;
                border-radius: 5px;
                font-weight: 600;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #216746;
            }
            """
        )