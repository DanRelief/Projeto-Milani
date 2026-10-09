from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QTextEdit,
    QMessageBox,
)

from .dialogo_padrao import DialogoPadrao


class CadastrarProcedimentoDialog(DialogoPadrao):
    def __init__(self, paciente: dict, parent=None) -> None:
        super().__init__("CADASTRAR PROCEDIMENTO", parent)

        self.procedimento_input = self._criar_campo(
            "Procedimento:",
            "",
        )

        self.medico_input = self._criar_campo(
            "Médico responsável:",
            paciente.get("medico_procedimento", ""),
        )

        self.data_input = QDateEdit()
        self.data_input.setCalendarPopup(True)
        self.data_input.setDate(QDate.currentDate())

        self.hora_input = QTimeEdit()
        self.hora_input.setTime(QTime.currentTime())

        self.observacoes_input = QTextEdit()
        self.observacoes_input.setPlaceholderText(
            "Digite observações sobre o procedimento..."
        )

        self._adicionar_campo("Data:", self.data_input)
        self._adicionar_campo("Hora:", self.hora_input)
        self._adicionar_campo("Observações:", self.observacoes_input)

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
        if not self.procedimento_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo obrigatório",
                "Informe o procedimento.",
            )
            return False

        return True

    def dados(self) -> dict:
        return {
            "tipo": "Procedimento",
            "procedimento": self.procedimento_input.text().strip(),
            "medico_procedimento": self.medico_input.text().strip(),
            "data": self.data_input.date().toString("dd/MM/yyyy"),
            "hora": self.hora_input.time().toString("HH:mm"),
            "observacoes": self.observacoes_input.toPlainText().strip(),
        }