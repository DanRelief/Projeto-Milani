from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DialogoPadrao(QDialog):
    """Base visual e comportamental dos popups da aplicação."""

    def __init__(self, titulo: str, parent=None) -> None:
        super().__init__(parent)

        self._pode_fechar = False
        self._overlay = None

        self.setObjectName("dialogo_padrao")
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedWidth(600)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 20)
        layout_principal.setSpacing(10)

        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("titulo_dialogo")
        layout_principal.addWidget(titulo_label)

        self.layout_conteudo = QVBoxLayout()
        self.layout_conteudo.setSpacing(5)
        layout_principal.addLayout(self.layout_conteudo)

        layout_botoes = QHBoxLayout()
        layout_botoes.setContentsMargins(8, 20, 8, 0)

        self.botao_cancelar = QPushButton("Cancelar")
        self.botao_salvar = QPushButton("Salvar")

        self.botao_cancelar.setObjectName("botao_acao")
        self.botao_salvar.setObjectName("botao_acao")

        self.botao_cancelar.clicked.connect(self._cancelar)
        self.botao_salvar.clicked.connect(self._salvar)

        layout_botoes.addWidget(self.botao_cancelar)
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.botao_salvar)
        layout_principal.addLayout(layout_botoes)

        self.setStyleSheet(
            """
            QDialog#dialogo_padrao {
                background-color: white;
                border-radius: 12px;
            }

            QLabel#titulo_dialogo {
                color: #08b9df;
                font-size: 26px;
                font-weight: bold;
            }

            QLabel#rotulo_campo {
                color: #08b9df;
                font-size: 22px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #b8b8b8;
                color: white;
                border: none;
                border-radius: 10px;
                min-height: 40px;
                padding: 0 10px;
                font-size: 20px;
            }

            QRadioButton#cartao_escolha {
                background-color: white;
                color: #08b9df;
                border: 2px solid transparent;
                border-radius: 10px;
                padding: 10px 14px;
                min-height: 28px;
                font-size: 18px;
                font-weight: bold;
            }
            
            QRadioButton#cartao_escolha:hover {
                background-color: #f0fcff;
            }

            QRadioButton#cartao_escolha:checked {
                border: 2px solid #08b9df;
                background-color: white;
            }

            QRadioButton#cartao_escolha::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #d0d0d0;
                background-color: #e5e5e5;
            }

            QRadioButton#cartao_escolha::indicator:hover {
                border-color: #08b9df;
            }

            QRadioButton#cartao_escolha::indicator:checked {
                background-color: #08b9df;
                border: 2px solid #08b9df;
            }

            #modal_overlay {
                background-color: rgba(0, 0, 0, 155);
            }

            QComboBox {
                background-color: #b8b8b8;
                color: white;
                border: none;
                border-radius: 10px;
                min-height: 40px;
                padding: 0 12px;
                font-size: 20px;
            }

            QComboBox:hover {
                background-color: #a9a9a9;
            }

            QComboBox::drop-down {
                border: none;
                width: 35px;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                color: #08b9df;
                selection-background-color: #08b9df;
                selection-color: white;
                font-size: 18px;
            }

            """
        )

    def exec(self) -> int:
        """Exibe o diálogo com a janela-pai escurecida e bloqueada."""
        parent = self.parentWidget()

        if parent is not None:
            self._overlay = QWidget(parent)
            self._overlay.setObjectName("modal_overlay")
            self._overlay.setGeometry(parent.rect())

            self._overlay.setStyleSheet(
                "background-color: rgba(0, 0, 0, 155);"
            )
            self._overlay.show()
            self._overlay.raise_()

            self.adjustSize()
            self.move(parent.frameGeometry().center() - self.rect().center())

        resultado = super().exec()

        if self._overlay is not None:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

        return resultado

    def validar(self) -> bool:
        return True

    def _cancelar(self) -> None:
        self._pode_fechar = True
        super().reject()

    def _salvar(self) -> None:
        if self.validar():
            self._pode_fechar = True
            super().accept()

    def reject(self) -> None:
        if self._pode_fechar:
            super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._pode_fechar:
            event.accept()
        else:
            event.ignore()
