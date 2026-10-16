from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal
from ..infrastructure.database import listar_animais

class DialogSelecionarAnimal(QDialog):
    animal_selecionado = Signal(dict, bool) # (dados_animal, e_proprietario)

    def __init__(self, usuario_logado: dict, parent=None):
        super().__init__(parent)
        self.usuario_logado = usuario_logado
        self.setWindowTitle("Selecionar Animal para Monitorar")
        self.setMinimumSize(650, 350)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Selecione um animal cadastrado na rede:"))

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "Espécie", "Estado", "Procedimento", "Responsável"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabela)

        btn_monitorar = QPushButton("Iniciar Monitoramento")
        btn_monitorar.clicked.connect(self._confirmar_selecao)
        layout.addWidget(btn_monitorar)

        self.setLayout(layout)
        self._carregar_dados()

    def _carregar_dados(self):
        self.animais = listar_animais()
        self.tabela.setRowCount(len(self.animais))

        for i, a in enumerate(self.animais):
            self.tabela.setItem(i, 0, QTableWidgetItem(str(a["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(a["nome"]))
            self.tabela.setItem(i, 2, QTableWidgetItem(a["especie"]))
            self.tabela.setItem(i, 3, QTableWidgetItem(a["estado_clinico"]))
            self.tabela.setItem(i, 4, QTableWidgetItem(a["procedimento"]))
            self.tabela.setItem(i, 5, QTableWidgetItem(a["nome_responsavel"]))

    def _confirmar_selecao(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um animal na tabela.")
            return

        animal = self.animais[row]
        # Verifica se o animal pertence ao aluno logado
        e_proprietario = (animal["responsavel_aplicacao"] == self.usuario_logado.get("id"))
        
        self.animal_selecionado.emit(animal, e_proprietario)
        self.accept()