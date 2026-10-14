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
from . .database import autenticar_usuario
from PySide6.QtWidgets import QListView


class TelaLogin(QMainWindow):
    """Janela de login com autenticação via banco de dados MySQL."""

    authenticated = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A. - Login")
        self.setMinimumSize(420, 300)

        self.role_combo = QComboBox()
        self.role_combo.setView(QListView())
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
            QMainWindow { 
                background-color: #f7f9fc; 
            }
            QLabel { 
                color: #2c3e50; 
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#title { 
                color: #1f4d3a; 
                font-size: 20px; 
                font-weight: 700; 
            }
            QLineEdit, QComboBox {
                min-height: 32px;
                padding: 2px 10px;
                border: 1px solid #c7d0d9;
                border-radius: 6px;
                background-color: #ffffff;
                color: #1a1a1a;  /* Garante texto escuro visível ao digitar */
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #287a55;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #c7d0d9;
                background-color: #ffffff;    
                color: #1a1a1a;               
                selection-background-color: #287a55; 
                selection-color: #ffffff;     
                padding: 4px;
                outline: 0px;
            }
            QPushButton {
                min-height: 36px;
                color: #ffffff;
                background-color: #287a55;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { 
                background-color: #216746; 
            }
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
        """Autentica o usuário consultando o banco MySQL."""
        # Consulta o banco de dados MySQL
        usuario = autenticar_usuario(role, identifier, password)

        if usuario is None:
            return False

        # Monta o dicionário de sessão padronizado para a TelaInicial
        session = {
            "name": usuario.get("nome", ""),
            "role": "Aluno" if role == "student" else "Docente",
            "identifier_label": "RA" if role == "student" else "E-mail",
            "identifier": usuario.get("identificador", identifier),
        }

        self.authenticated.emit(session)
        return True

    def _handle_login(self) -> None:
        """Valida e processa o envio do formulário de login."""
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
        
        # Chama a autenticação com o MySQL
        if not self.authenticate(role, identifier, password):
            QMessageBox.warning(
                self,
                "Login inválido",
                "Verifique o perfil, o identificador e a senha.",
            )