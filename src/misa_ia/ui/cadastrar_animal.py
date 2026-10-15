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

# Importação relativa ajustada para acessar database.py um nível acima (misa_ia/)
from ..database import cadastrar_animal


class DialogCadastrarAnimal(QDialog):
    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(parent)
        self.usuario_logado = usuario_logado
        self.setWindowTitle("Cadastrar Novo Animal - M.I.S.A.")
        self.setMinimumSize(400, 440)

        layout = QVBoxLayout()
        title = QLabel("Cadastro de Animal")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1f4d3a;")
        layout.addWidget(title)

        form = QFormLayout()

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: Rex, Thor...")

        self.input_especie = QLineEdit()
        self.input_especie.setPlaceholderText("Ex: Canina, Felina, Equina...")

        self.input_idade = QSpinBox()
        self.input_idade.setRange(0, 100)

        # Configuração do Porte alinhada ao ENUM do MySQL ('pequeno', 'medio', 'grande')
        self.combo_porte = QComboBox()
        self.combo_porte.setView(QListView())
        self.combo_porte.addItem("Pequeno", "pequeno")
        self.combo_porte.addItem("Médio", "medio")
        self.combo_porte.addItem("Grande", "grande")

        self.input_procedimento = QLineEdit()
        self.input_procedimento.setPlaceholderText("Ex: Pós-operatório, Monitoramento...")

        # Configuração do Estado Clínico alinhada ao ENUM do MySQL ('estavel', 'moderado', 'grave')
        self.combo_estado = QComboBox()
        self.combo_estado.setView(QListView())
        self.combo_estado.addItem("Estável", "estavel")
        self.combo_estado.addItem("Moderado", "moderado")
        self.combo_estado.addItem("Grave", "grave")

        self.input_medicacao = QLineEdit()
        self.input_medicacao.setPlaceholderText("Ex: Dipirona, Antibiótico...")

        self.input_quantidade = QLineEdit()
        self.input_quantidade.setPlaceholderText("Ex: 2ml, 1 comprimido...")

        form.addRow("Nome:", self.input_nome)
        form.addRow("Espécie:", self.input_especie)
        form.addRow("Idade (anos):", self.input_idade)
        form.addRow("Porte:", self.combo_porte)
        form.addRow("Procedimento:", self.input_procedimento)
        form.addRow("Estado Clínico:", self.combo_estado)
        form.addRow("Última Medicação:", self.input_medicacao)
        form.addRow("Dose/Quantidade:", self.input_quantidade)

        layout.addLayout(form)

        btn_salvar = QPushButton("Salvar Cadastro")
        btn_salvar.clicked.connect(self._salvar)
        layout.addWidget(btn_salvar)

        self.setLayout(layout)
        self._aplicar_estilo()

    def _salvar(self):
        nome = self.input_nome.text().strip()
        especie = self.input_especie.text().strip()
        procedimento = self.input_procedimento.text().strip()

        if not nome or not especie or not procedimento:
            QMessageBox.warning(self, "Aviso", "Preencha os campos obrigatórios: Nome, Espécie e Procedimento.")
            return
        
        usuario_id = self.usuario_logado.get("id") or self.usuario_logado.get("usuario_id")
        
        if not usuario_id:
            QMessageBox.critical(self, "Erro de Sessão", "Não foi possível recuperar o ID do usuário logado.")
            return

        # Prepara o dicionário com os dados exatamente no formato esperado pelo MySQL
        dados = {
            "nome": nome,
            "especie": especie,
            "idade": self.input_idade.value(),
            "porte": self.combo_porte.currentData(),  # Retorna 'pequeno', 'medio' ou 'grande'
            "procedimento": procedimento,
            "estado_clinico": self.combo_estado.currentData(),  # Retorna 'estavel', 'moderado' ou 'grave'
            "ultima_medicacao": self.input_medicacao.text().strip() or None,
            "quantidade": self.input_quantidade.text().strip() or None,
            "responsavel_aplicacao": usuario_id  # ID da FK referente à tabela usuarios
        }

        sucesso, msg = cadastrar_animal(dados)
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro ao Salvar", msg)

    def _aplicar_estilo(self):
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
            QLineEdit, QComboBox, QSpinBox {
                min-height: 28px; 
                padding: 2px 8px; 
                border: 1px solid #c7d0d9;
                border-radius: 5px; 
                background: white; 
                color: #1a1a1a;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
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