from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..database import autenticar_usuario, cadastrar_usuario


class TelaLogin(QMainWindow):
    """Janela de autenticação e cadastro de usuários no M.I.S.A."""

    authenticated = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A. - Acesso ao Sistema")
        self.setMinimumSize(420, 380)

        # Widget de Abas (Login / Criar Conta)
        self.tabs = QTabWidget()

        # Construção da Aba de Login e da Aba de Cadastro
        self.tab_login = self._criar_aba_login()
        self.tab_cadastro = self._criar_aba_cadastro()

        self.tabs.addTab(self.tab_login, "Fazer Login")
        self.tabs.addTab(self.tab_cadastro, "Criar Conta")

        title = QLabel("Monitoramento Inteligente de Saúde Animal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")

        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(self.tabs)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self._aplicar_estilos()

    def _criar_aba_login(self) -> QWidget:
        widget = QWidget()

        self.login_role_combo = QComboBox()
        self.login_role_combo.setView(QListView())
        self.login_role_combo.addItem("Aluno", "student")
        self.login_role_combo.addItem("Docente", "teacher")

        self.login_identifier_input = QLineEdit()
        self.login_identifier_input.setPlaceholderText("Digite seu RA")

        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Digite sua senha")
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_role_combo.currentIndexChanged.connect(
            lambda idx: self._atualizar_label(
                idx, self.login_role_combo, self.login_identifier_input, form
            )
        )

        login_button = QPushButton("Entrar")
        login_button.clicked.connect(self._handle_login)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Perfil:", self.login_role_combo)
        form.addRow("RA:", self.login_identifier_input)
        form.addRow("Senha:", self.login_password_input)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(14)
        layout.addLayout(form)
        layout.addSpacing(10)
        layout.addWidget(login_button)

        widget.setLayout(layout)
        return widget

    def _criar_aba_cadastro(self) -> QWidget:
        widget = QWidget()

        self.cad_role_combo = QComboBox()
        self.cad_role_combo.setView(QListView())
        self.cad_role_combo.addItem("Aluno", "student")
        self.cad_role_combo.addItem("Docente", "teacher")

        self.cad_name_input = QLineEdit()
        self.cad_name_input.setPlaceholderText("Digite seu nome completo")

        self.cad_identifier_input = QLineEdit()
        self.cad_identifier_input.setPlaceholderText("Digite seu RA")

        self.cad_password_input = QLineEdit()
        self.cad_password_input.setPlaceholderText("Crie uma senha")
        self.cad_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.cad_role_combo.currentIndexChanged.connect(
            lambda idx: self._atualizar_label(
                idx, self.cad_role_combo, self.cad_identifier_input, form
            )
        )

        cad_button = QPushButton("Cadastrar e Salvar")
        cad_button.clicked.connect(self._handle_cadastro)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Perfil:", self.cad_role_combo)
        form.addRow("Nome:", self.cad_name_input)
        form.addRow("RA:", self.cad_identifier_input)
        form.addRow("Senha:", self.cad_password_input)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(form)
        layout.addSpacing(6)
        layout.addWidget(cad_button)

        widget.setLayout(layout)
        return widget

    def _atualizar_label(self, index: int, combo: QComboBox, input_field: QLineEdit, form: QFormLayout) -> None:
        is_student = combo.itemData(index) == "student"
        label = form.labelForField(input_field)
        if label is not None:
            label.setText("RA:" if is_student else "E-mail:")
        input_field.setPlaceholderText("Digite seu RA" if is_student else "Digite seu e-mail")

    def authenticate(self, role: str, identifier: str, password: str) -> bool:
        usuario = autenticar_usuario(role, identifier, password)
        if usuario is None:
            return False

        session = {
            "name": usuario.get("nome", ""),
            "role": "Aluno" if role == "student" else "Docente",
            "identifier_label": "RA" if role == "student" else "E-mail",
            "identifier": usuario.get("identificador", identifier),
        }
        self.authenticated.emit(session)
        return True

    def _handle_login(self) -> None:
        identifier = self.login_identifier_input.text().strip()
        password = self.login_password_input.text()
        role = self.login_role_combo.currentData()

        if not identifier or not password:
            QMessageBox.warning(self, "Campos Obrigatórios", "Preencha o identificador e a senha.")
            return

        if not self.authenticate(role, identifier, password):
            QMessageBox.warning(self, "Erro de Login", "Perfil, identificador ou senha incorretos.")

    def _handle_cadastro(self) -> None:
        nome = self.cad_name_input.text().strip()
        identifier = self.cad_identifier_input.text().strip()
        password = self.cad_password_input.text()
        role = self.cad_role_combo.currentData()

        if not nome or not identifier or not password:
            QMessageBox.warning(self, "Campos Obrigatórios", "Preencha todos os campos para cadastrar.")
            return

        sucesso, mensagem = cadastrar_usuario(nome, role, identifier, password)

        if sucesso:
            QMessageBox.information(
                self,
                "Sucesso",
                "Conta criada com sucesso! Agora você pode fazer login.",
            )
            # Limpa os campos de cadastro
            self.cad_name_input.clear()
            self.cad_identifier_input.clear()
            self.cad_password_input.clear()

            # Preenche automaticamente a aba de login e altera para ela
            self.login_role_combo.setCurrentIndex(self.cad_role_combo.currentIndex())
            self.login_identifier_input.setText(identifier)
            self.tabs.setCurrentIndex(0)  # Alterna para a aba "Fazer Login"
        else:
            QMessageBox.warning(self, "Erro no Cadastro", mensagem)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #f7f9fc; }
            QLabel { color: #2c3e50; font-size: 13px; font-weight: 500; }
            QLabel#title { color: #1f4d3a; font-size: 18px; font-weight: 700; }
            
            QTabWidget::pane { border: 1px solid #c7d0d9; background: #ffffff; border-radius: 6px; }
            QTabBar::tab {
                background: #e9ecef;
                color: #495057;
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #287a55;
                border-bottom: 2px solid #287a55;
            }

            QLineEdit, QComboBox {
                min-height: 30px;
                padding: 2px 10px;
                border: 1px solid #c7d0d9;
                border-radius: 6px;
                background-color: #ffffff;
                color: #1a1a1a;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #287a55; }

            QComboBox QAbstractItemView {
                border: 1px solid #c7d0d9;
                background-color: #ffffff;
                color: #1a1a1a;
                selection-background-color: #287a55;
                selection-color: #ffffff;
                padding: 4px;
            }

            QPushButton {
                min-height: 34px;
                color: #ffffff;
                background-color: #287a55;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #216746; }
            """
        )