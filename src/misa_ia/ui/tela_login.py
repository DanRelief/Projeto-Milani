from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TelaLogin(QMainWindow):
    """Janela de login com autenticação simulada em memória."""

    authenticated = Signal(dict)

    # Usuários fictícios usados somente para simular a autenticação.
    _FAKE_USERS = {
        ("student", "1115152"): {
            "name": "Bryan",
            "role": "Aluno",
            "identifier_label": "RA",
            "identifier": "1115152",
            "password": "1234",
        },
        ("teacher", "milani@misa.local"): {
            "name": "Milani",
            "role": "Docente",
            "identifier_label": "E-mail",
            "identifier": "milani@misa.local",
            "password": "1234",
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A. - Login")
        self.setMinimumSize(420, 300)

        self.role_combo = QComboBox()
        self.role_combo.addItem("Aluno", "student")
        self.role_combo.addItem("Docente", "teacher")
        self.role_combo.currentIndexChanged.connect(self._update_identifier_field)

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Digite seu RA")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Digite sua senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self._handle_login)

        title = QLabel("Monitoramento Inteligente de Saúde Animal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")

        subtitle = QLabel("Entre para acessar o sistema")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Perfil:", self.role_combo)
        form.addRow("RA:", self.identifier_input)
        form.addRow("Senha:", self.password_input)

        layout = QVBoxLayout()
        layout.setContentsMargins(48, 32, 48, 32)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addSpacing(8)
        layout.addWidget(self.login_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setStyleSheet(
            """
            QMainWindow { background-color: #f7f9fc; }
            QLabel#title { color: #1f4d3a; font-size: 20px; font-weight: 600; }
            QLineEdit, QComboBox {
                min-height: 30px;
                padding: 2px 8px;
                border: 1px solid #c7d0d9;
                border-radius: 5px;
                background-color: white;
            }
            QPushButton {
                min-height: 34px;
                color: white;
                background-color: #287a55;
                border: none;
                border-radius: 5px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #216746; }
            """
        )

    def _update_identifier_field(self, index: int) -> None:
        """Atualiza o rótulo e o exemplo conforme o perfil escolhido."""
        is_student = self.role_combo.itemData(index) == "student"
        label = self.centralWidget().layout().itemAt(3).layout().labelForField(
            self.identifier_input
        )
        if label is not None:
            label.setText("RA:" if is_student else "E-mail:")
        self.identifier_input.setPlaceholderText(
            "Digite seu RA" if is_student else "Digite seu e-mail"
        )

    def authenticate(self, role: str, identifier: str, password: str) -> bool:
        """Autentica uma sessão e retorna se as credenciais são válidas."""
        user = self._FAKE_USERS.get((role, identifier))
        if user is None or user["password"] != password:
            return False

        session = {key: value for key, value in user.items() if key != "password"}
        self.authenticated.emit(session)
        return True

    def _handle_login(self) -> None:
        """Valida o usuário contra a tabela fictícia de autenticação."""
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text()

        if not identifier or not password:
            QMessageBox.warning(
                self,
                "Campos obrigatórios",
                "Preencha o identificador e a senha para continuar.",
            )
            return

        role = self.role_combo.currentData()
        user = self._FAKE_USERS.get((role, identifier))

        if user is None or user["password"] != password:
            QMessageBox.warning(
                self,
                "Login inválido",
                "Verifique o perfil, o identificador e a senha.",
            )
            return

        # Envia somente os dados necessários para montar a sessão da tela inicial.
        session = {key: value for key, value in user.items() if key != "password"}
        self.authenticated.emit(session)
