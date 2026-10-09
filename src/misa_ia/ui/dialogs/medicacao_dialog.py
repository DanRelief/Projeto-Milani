from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
)

from .dialogo_padrao import DialogoPadrao


class CadastrarMedicacaoDialog(DialogoPadrao):
    def __init__(self, paciente: dict, parent=None) -> None:
        super().__init__("CADASTRAR MEDICAÇÃO", parent)

        self.medicacao_input = self._criar_campo(
            "Medicação:",
            "",
        )

        self.quantidade_input = self._criar_campo(
            "Quantidade:",
            "",
        )

        rotulo_unidade = QLabel("Unidade:")
        rotulo_unidade.setObjectName("rotulo_campo")
        self.layout_conteudo.addWidget(rotulo_unidade)

        self.unidade_combo = QComboBox()
        self.unidade_combo.addItems([
            "mg",
            "ml",
            "comprimido",
            "gotas",
        ])
        self.layout_conteudo.addWidget(self.unidade_combo)

        self.medico_input = self._criar_campo(
            "Responsável pela aplicação:",
            paciente.get("medico_medicacao", ""),
        )

        self.data_input = QDateEdit()
        self.data_input.setCalendarPopup(True)
        self.data_input.setDate(QDate.currentDate())

        self.hora_input = QTimeEdit()
        self.hora_input.setTime(QTime.currentTime())

        self._adicionar_campo("Data:", self.data_input)
        self._adicionar_campo("Hora:", self.hora_input)

    def _criar_campo(self, titulo: str, valor: str) -> QLineEdit:
        campo = QLineEdit()
        campo.setText(valor)
        self._adicionar_campo(titulo, campo)
        return campo

    def _adicionar_campo(self, titulo: str, campo) -> None:
        rotulo = QLabel(titulo)
        rotulo.setObjectName("rotulo_campo")

        self.layout_conteudo.addWidget(rotulo)
        self.layout_conteudo.addWidget(campo)

    def validar(self) -> bool:
        if not self.medicacao_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo obrigatório",
                "Informe a medicação.",
            )
            return False

        if not self.quantidade_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo obrigatório",
                "Informe a quantidade.",
            )
            return False

        return True

    def dados(self) -> dict:
        return {
            "tipo": "Medicação",
            "medicacao": self.medicacao_input.text().strip(),
            "quantidade": self.quantidade_input.text().strip(),
            "unidade": self.unidade_combo.currentText(),
            "medico_medicacao": self.medico_input.text().strip(),
            "data": self.data_input.date().toString("dd/MM/yyyy"),
            "hora": self.hora_input.time().toString("HH:mm"),
        }