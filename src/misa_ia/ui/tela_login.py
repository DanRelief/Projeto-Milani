from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSize,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsColorizeEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..database import autenticar_usuario, cadastrar_usuario


class _ImagemComCorte(QLabel):
    """Exibe uma imagem preenchendo o espaço sem deformá-la."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_image(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - assinatura do Qt
        if self._pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        device_ratio = max(1.0, self.devicePixelRatioF())
        render_size = QSize(
            max(1, round(self.width() * device_ratio)),
            max(1, round(self.height() * device_ratio)),
        )
        scaled = self._pixmap.scaled(
            render_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(device_ratio)
        logical_width = scaled.width() / device_ratio
        logical_height = scaled.height() / device_ratio
        x = round((self.width() - logical_width) / 2)
        y = round((self.height() - logical_height) / 2)
        painter.drawPixmap(x, y, scaled)


class _GradienteSobreImagem(QWidget):
    """Cria a transição visual entre a foto e o painel ciano."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:  # noqa: N802 - assinatura do Qt
        painter = QPainter(self)
        gradient = QLinearGradient(self.width() * 0.52, 0, self.width(), 0)
        blue = QColor("#11bad2")
        gradient.setColorAt(0.0, QColor(blue.red(), blue.green(), blue.blue(), 0))
        gradient.setColorAt(0.72, QColor(blue.red(), blue.green(), blue.blue(), 145))
        gradient.setColorAt(1.0, blue)
        painter.fillRect(self.rect(), gradient)


class _CarrosselDeImagens(QWidget):
    """Alterna os assets vet* com uma transição suave de opacidade."""

    def __init__(self, image_paths: list[Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("image_panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(360)

        self._images = [QPixmap(str(path)) for path in image_paths if path.exists()]
        self._labels = [_ImagemComCorte(self), _ImagemComCorte(self)]
        self._gradient = _GradienteSobreImagem(self)
        self._gradient.setGeometry(self.rect())
        self._gradient.raise_()
        self._effects = [QGraphicsOpacityEffect(label) for label in self._labels]
        for label, effect in zip(self._labels, self._effects):
            label.setGraphicsEffect(effect)
            label.hide()

        self._active_index = 0
        self._image_index = 0
        self._animation: QParallelAnimationGroup | None = None
        if self._images:
            self._labels[0].set_image(self._images[0])
            self._effects[0].setOpacity(1.0)
            self._labels[0].show()

        self._timer = QTimer(self)
        self._timer.setInterval(7000)
        self._timer.timeout.connect(self._show_next_image)
        if len(self._images) > 1:
            self._timer.start()

    def resizeEvent(self, event) -> None:  # noqa: N802 - assinatura do Qt
        for label in self._labels:
            label.setGeometry(self.rect())
        self._gradient.setGeometry(self.rect())
        self._gradient.raise_()
        super().resizeEvent(event)

    def _show_next_image(self) -> None:
        if len(self._images) < 2 or self._animation is not None:
            return

        next_index = (self._image_index + 1) % len(self._images)
        incoming_index = 1 - self._active_index
        outgoing = self._effects[self._active_index]
        incoming = self._effects[incoming_index]
        incoming_label = self._labels[incoming_index]

        incoming_label.set_image(self._images[next_index])
        incoming.setOpacity(0.0)
        incoming_label.show()

        fade_out = QPropertyAnimation(outgoing, b"opacity", self)
        fade_out.setDuration(1100)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

        fade_in = QPropertyAnimation(incoming, b"opacity", self)
        fade_in.setDuration(1100)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._animation = QParallelAnimationGroup(self)
        self._animation.addAnimation(fade_out)
        self._animation.addAnimation(fade_in)
        self._animation.finished.connect(
            lambda: self._finish_transition(incoming_index, next_index)
        )
        self._animation.start()

    def _finish_transition(self, incoming_index: int, image_index: int) -> None:
        self._labels[self._active_index].hide()
        self._effects[self._active_index].setOpacity(0.0)
        self._effects[incoming_index].setOpacity(1.0)
        self._active_index = incoming_index
        self._image_index = image_index
        self._animation = None

    def closeEvent(self, event) -> None:  # noqa: N802 - assinatura do Qt
        self._timer.stop()
        super().closeEvent(event)


class TelaLogin(QMainWindow):
    """Tela de login e cadastro de usuários do M.I.S.A."""

    authenticated = Signal(dict)
    # Altere este valor para aumentar ou reduzir a logo.
    LOGO_SIZE = 190

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A. - Login")
        self.setMinimumSize(900, 560)
        self.resize(1120, 680)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("auth_tabs")
        self.tabs.tabBar().hide()
        self.tab_login = self._criar_aba_login()
        self.tab_cadastro = self._criar_aba_cadastro()
        self.tabs.addTab(self.tab_login, "Fazer Login")
        self.tabs.addTab(self.tab_cadastro, "Criar Conta")
        self.tabs.setCurrentIndex(0)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tabs.setMaximumWidth(760)

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

        # Inclui obrigatoriamente o 'id' do usuário cadastrado no MySQL
        session = {
            "id": usuario.get("id"),  # <-- CAMPO ESSENCIAL PARA A CHAVE ESTRANGEIRA
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
                "Conta criada com sucesso! Realizando login...",
            )
            # Tenta autenticar imediatamente após cadastrar para obter o ID
            self.authenticate(role, identifier, password)
        else:
            QMessageBox.warning(self, "Erro no Cadastro", mensagem)

    def _aplicar_estilos(self) -> None:
        self.role_combo = QComboBox()
        self.role_combo.addItem("Aluno", "student")
        self.role_combo.addItem("Docente", "teacher")
        self.role_combo.setObjectName("role_selector")
        self.role_combo.setMinimumHeight(28)
        self.role_combo.setMinimumWidth(110)
        self.role_combo.currentIndexChanged.connect(self._update_identifier_field)

        self.identifier_input = QLineEdit()
        self.identifier_input.setObjectName("login_field")
        self.identifier_input.setPlaceholderText("Digite seu RA")
        self.identifier_input.setMinimumHeight(40)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("login_field")
        self.password_input.setPlaceholderText("Digite sua senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)

        self.login_button = QPushButton("Entrar")
        self.login_button.setObjectName("botao_acao")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)

        cadastro_button = QPushButton("Não tem login? Cadastre-se")
        cadastro_button.setObjectName("register_link")
        cadastro_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cadastro_button.clicked.connect(self._show_registration_message)

        assets_dir = Path(__file__).resolve().parents[3] / "assets"
        image_paths = sorted(
            path
            for path in assets_dir.glob("vet*")
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        image_panel = _CarrosselDeImagens(image_paths)

        logo_label = QLabel()
        logo_label.setObjectName("misa_logo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedSize(self.LOGO_SIZE, self.LOGO_SIZE)
        logo_path = assets_dir / "logo_misa.png"
        logo = QPixmap(str(logo_path))
        if not logo.isNull():
            logo_label.setPixmap(
                logo.scaled(
                    self.LOGO_SIZE,
                    self.LOGO_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo_effect = QGraphicsColorizeEffect(logo_label)
            logo_effect.setColor(Qt.GlobalColor.white)
            logo_effect.setStrength(1.0)
            logo_label.setGraphicsEffect(logo_effect)

        logo_caption = QLabel("M.I.S.A.")
        logo_caption.setObjectName("logo_caption")
        logo_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(58, 34, 58, 20)
        right_layout.addStretch(1)
        right_layout.addWidget(self.tabs)
        right_layout.addSpacing(18)
        right_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addWidget(logo_caption, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch(1)

        page = QWidget()
        page.setObjectName("login_page")
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(image_panel, 1)
        page_layout.addWidget(right_panel, 1)
        self.setCentralWidget(page)
        self._aplicar_estilos()

    def _criar_aba_login(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("login_card")

        welcome = QLabel("Bem-vindo ao MISA")
        welcome.setObjectName("welcome_title")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.login_role_combo = QComboBox()
        self.login_role_combo.setObjectName("role_selector")
        self.login_role_combo.setMinimumHeight(28)
        self.login_role_combo.setMinimumWidth(110)
        self.login_role_combo.addItem("Aluno", "student")
        self.login_role_combo.addItem("Docente", "teacher")

        profile_row = QHBoxLayout()
        profile_row.setContentsMargins(0, 0, 0, 0)
        profile_row.addStretch()
        profile_caption = QLabel("TIPO DE ACESSO")
        profile_caption.setObjectName("profile_caption")
        profile_row.addWidget(profile_caption)
        profile_row.addWidget(self.login_role_combo)

        self.login_identifier_input = QLineEdit()
        self.login_identifier_input.setObjectName("login_field")
        self.login_identifier_input.setPlaceholderText("Digite seu RA")
        self.login_identifier_input.setMinimumHeight(40)

        self.login_password_input = QLineEdit()
        self.login_password_input.setObjectName("login_field")
        self.login_password_input.setPlaceholderText("Digite sua senha")
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password_input.setMinimumHeight(40)

        self._login_identifier_label = QLabel("RA")
        self._login_identifier_label.setObjectName("field_label")
        password_label = QLabel("SENHA")
        password_label.setObjectName("field_label")

        self.login_button = QPushButton("Entrar")
        self.login_button.setObjectName("botao_acao")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self._handle_login)
        self.login_password_input.returnPressed.connect(self._handle_login)

        cadastro_button = QPushButton("Não tem login? Cadastre-se")
        cadastro_button.setObjectName("register_link")
        cadastro_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cadastro_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        form_layout = QVBoxLayout()
        form_layout.setSpacing(7)
        form_layout.addWidget(self._login_identifier_label)
        form_layout.addWidget(self.login_identifier_input)
        form_layout.addSpacing(8)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.login_password_input)
        form_layout.addSpacing(17)
        form_layout.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        form_layout.addSpacing(67)
        form_layout.addWidget(cadastro_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 26, 32, 24)
        layout.setSpacing(0)
        layout.addWidget(welcome)
        layout.addSpacing(25)
        layout.addLayout(profile_row)
        layout.addSpacing(11)
        layout.addLayout(form_layout)

        # Aliases mantidos para compatibilidade com o fluxo de auto-login existente.
        self.role_combo = self.login_role_combo
        self.identifier_input = self.login_identifier_input
        self.password_input = self.login_password_input
        self._identifier_label = self._login_identifier_label
        self.login_role_combo.currentIndexChanged.connect(self._update_identifier_field)
        return widget

    def _criar_aba_cadastro(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("register_card")

        title = QLabel("Criar conta")
        title.setObjectName("welcome_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cad_role_combo = QComboBox()
        self.cad_role_combo.setObjectName("role_selector")
        self.cad_role_combo.addItem("Aluno", "student")
        self.cad_role_combo.addItem("Docente", "teacher")
        self.cad_role_combo.setMinimumHeight(32)

        self.cad_name_input = QLineEdit()
        self.cad_name_input.setObjectName("login_field")
        self.cad_name_input.setPlaceholderText("Digite seu nome completo")
        self.cad_name_input.setMinimumHeight(40)

        self.cad_identifier_input = QLineEdit()
        self.cad_identifier_input.setObjectName("login_field")
        self.cad_identifier_input.setPlaceholderText("Digite seu RA")
        self.cad_identifier_input.setMinimumHeight(40)

        self.cad_password_input = QLineEdit()
        self.cad_password_input.setObjectName("login_field")
        self.cad_password_input.setPlaceholderText("Crie uma senha")
        self.cad_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.cad_password_input.setMinimumHeight(40)

        role_label = QLabel("TIPO DE ACESSO")
        role_label.setObjectName("field_label_small")
        name_label = QLabel("NOME")
        name_label.setObjectName("field_label_small")
        identifier_label = QLabel("RA / E-MAIL")
        identifier_label.setObjectName("field_label_small")
        password_label = QLabel("SENHA")
        password_label.setObjectName("field_label_small")

        cadastro_button = QPushButton("Cadastrar e salvar")
        cadastro_button.setObjectName("botao_acao")
        cadastro_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cadastro_button.clicked.connect(self._handle_cadastro)

        voltar_button = QPushButton("Voltar para o login")
        voltar_button.setObjectName("register_link")
        voltar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        voltar_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 26, 32, 24)
        layout.setSpacing(7)
        layout.addWidget(title)
        layout.addSpacing(12)
        layout.addWidget(role_label)
        layout.addWidget(self.cad_role_combo)
        layout.addWidget(name_label)
        layout.addWidget(self.cad_name_input)
        layout.addWidget(identifier_label)
        layout.addWidget(self.cad_identifier_input)
        layout.addWidget(password_label)
        layout.addWidget(self.cad_password_input)
        layout.addSpacing(15)
        layout.addWidget(cadastro_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(18)
        layout.addWidget(voltar_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.cad_role_combo.currentIndexChanged.connect(
            self._update_registration_identifier_field
        )
        return widget

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget#login_page, QWidget#image_panel,
            QWidget#right_panel {
                background-color: #11bad2;
            }
            QTabWidget#auth_tabs {
                background: transparent;
            }
            QTabWidget#auth_tabs::pane {
                border: none;
                background: transparent;
            }
            QWidget#login_card, QWidget#register_card {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
            }
            QLabel#welcome_title {
                color: #10b6d1;
                font-size: 32px;
                font-weight: 700;
            }
            QLabel#field_label {
                color: #0cb6d2;
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#field_label_small {
                color: #0cb6d2;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#profile_caption {
                color: #6f7780;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#logo_caption {
                color: #ffffff;
                font-size: 30px;
                font-weight: 700;
            }
            QComboBox#role_selector {
                color: #38444b;
                background-color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 2px 7px;
                min-height: 24px;
                min-width: 100px;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox#role_selector::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox#role_selector QAbstractItemView {
                color: #38444b;
                background-color: #ffffff;
                border: none;
                selection-background-color: #11bad2;
                selection-color: #ffffff;
                padding: 4px;
                outline: none;
            }
            QLineEdit#login_field {
                color: #41464a;
                background-color: #b6b6b6;
                border: 2px solid #b6b6b6;
                border-radius: 11px;
                padding: 0 12px;
                font-size: 16px;
            }
            QLineEdit#login_field:focus {
                border-color: #10b6d1;
                background-color: #c2c2c2;
            }
            QPushButton#botao_acao {
                background-color: #2100b8;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 6px 18px;
                min-height: 32px;
                font-size: 16px;
            }
            QPushButton#botao_acao:hover {
                background-color: #351bc9;
            }
            QPushButton#botao_acao:pressed {
                background-color: #180087;
            }
            QPushButton#register_link {
                color: #09afd0;
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: 700;
                text-decoration: underline;
            }
            QPushButton#register_link:hover {
                color: #087f9b;
            }
            """
        )

    def _update_identifier_field(self, index: int) -> None:
        """Atualiza o campo do login de acordo com o perfil selecionado."""
        is_student = self.login_role_combo.itemData(index) == "student"
        self._login_identifier_label.setText("RA" if is_student else "E-MAIL")
        self.login_identifier_input.setPlaceholderText(
            "Digite seu RA" if is_student else "Digite seu e-mail"
        )

    def _update_registration_identifier_field(self, index: int) -> None:
        """Atualiza o placeholder do identificador no cadastro."""
        is_student = self.cad_role_combo.itemData(index) == "student"
        self.cad_identifier_input.setPlaceholderText(
            "Digite seu RA" if is_student else "Digite seu e-mail"
        )

    def authenticate(self, role: str, identifier: str, password: str) -> bool:
        """Autentica no banco e emite a sessão criada pelo usuário."""
        usuario = autenticar_usuario(role, identifier, password)
        if usuario is None:
            return False

        session = {
            "name": usuario.get("nome", ""),
            "role": "Aluno" if role == "student" else "Docente",
            "identifier_label": "RA" if role == "student" else "E-mail",
            "identifier": usuario.get("identificador", identifier),
        }
        if "primeiro_acesso" in usuario:
            session["primeiro_acesso"] = usuario["primeiro_acesso"]
        self.authenticated.emit(session)
        return True

    def _handle_login(self) -> None:
        identifier = self.login_identifier_input.text().strip()
        password = self.login_password_input.text()
        role = self.login_role_combo.currentData()

        if not identifier or not password:
            QMessageBox.warning(
                self,
                "Campos obrigatórios",
                "Preencha o identificador e a senha.",
            )
            return

        if not self.authenticate(role, identifier, password):
            QMessageBox.warning(
                self,
                "Erro de Login",
                "Perfil, identificador ou senha incorretos.",
            )

    def _handle_cadastro(self) -> None:
        nome = self.cad_name_input.text().strip()
        identifier = self.cad_identifier_input.text().strip()
        password = self.cad_password_input.text()
        role = self.cad_role_combo.currentData()

        if not nome or not identifier or not password:
            QMessageBox.warning(
                self,
                "Campos obrigatórios",
                "Preencha todos os campos para cadastrar.",
            )
            return

        sucesso, mensagem = cadastrar_usuario(nome, role, identifier, password)
        if not sucesso:
            QMessageBox.warning(self, "Erro no Cadastro", mensagem)
            return

        QMessageBox.information(
            self,
            "Sucesso",
            "Conta criada com sucesso! Agora você pode fazer login.",
        )
        self.cad_name_input.clear()
        self.cad_identifier_input.clear()
        self.cad_password_input.clear()
        self.login_role_combo.setCurrentIndex(self.cad_role_combo.currentIndex())
        self.login_identifier_input.setText(identifier)
        self.tabs.setCurrentIndex(0)
