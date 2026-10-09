from PySide6.QtWidgets import QLabel, QTextBrowser
from PySide6.QtCore import Qt
from .dialogo_padrao import DialogoPadrao


class HistoricoDialog(DialogoPadrao):
    def __init__(self, historico: list[dict], parent=None) -> None:
        super().__init__("HISTÓRICO COMPLETO", parent)

        self.botao_salvar.hide()
        self.botao_cancelar.setText("Fechar")
        self.historico_view = QTextBrowser()
        self.historico_view.setReadOnly(True)

        self.historico_view.setMinimumHeight(260)

        self.historico_view.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                color: black;
                border: none;
                font-size: 16px;
                padding: 8px;
            }
        """)

        if not historico:
            self.historico_view.setPlainText(
                "Nenhum registro encontrado."
            )
        else:
            registros = []

            for registro in historico:
                registros.append(self._formatar_registro(registro))

            self.historico_view.setHtml("<hr>".join(registros))

        self.layout_conteudo.addWidget(self.historico_view)

    def _formatar_registro(self, registro: dict) -> str:
        if registro["tipo"] == "Procedimento":
            return (
                f"<b>Procedimento:</b> {registro['procedimento']}<br>"
                f"<b>Médico responsável:</b> "
                f"{registro['medico_procedimento']}<br>"
                f"<b>Data:</b> {registro['data']} "
                f"<b>Hora:</b> {registro['hora']}<br>"
                f"<b>Observações:</b> {registro['observacoes']}<br><br>"
            )

        return (
            f"<b>Medicação:</b> {registro['medicacao']}<br>"
            f"<b>Quantidade:</b> "
            f"{registro['quantidade']} {registro['unidade']}<br>"
            f"<b>Médico responsável:</b> "
            f"{registro['medico_medicacao']}<br>"
            f"<b>Data:</b> {registro['data']} "
            f"<b>Hora:</b> {registro['hora']}<br><br>"
        )