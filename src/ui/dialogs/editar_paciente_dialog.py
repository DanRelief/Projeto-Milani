from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QButtonGroup,QLabel,QLineEdit,QMessageBox,QRadioButton,QComboBox
from .dialogo_padrao import DialogoPadrao


class EditarPacienteDialog(DialogoPadrao):
    def __init__(self, paciente: dict, parent=None) -> None:
        super().__init__("EDITAR INFORMAÇÕES", parent)

        self.nome_input = self._criar_campo(
            "Nome:", paciente.get("nome", "")
        )

        self.especie_combo = self._criar_seletor("Espécie:",["Cachorro", "Gato", "Coelho", "Ave", "Outro"],paciente.get("especie", ""))
        
        self.idade_input = self._criar_campo(
            "Idade:", str(paciente.get("idade", ""))
        )
        self.idade_input.setValidator(QIntValidator(0, 100, self))

        rotulo_porte = QLabel("Porte:")
        rotulo_porte.setObjectName("rotulo_campo")
        self.layout_conteudo.addWidget(rotulo_porte)

        self.porte_group = QButtonGroup(self)

        for valor in ("Pequeno", "Médio", "Grande"):
            radio = QRadioButton(valor)
            radio.setObjectName("cartao_escolha")
            radio.setProperty("valor", valor)
            self.porte_group.addButton(radio)
            self.layout_conteudo.addWidget(radio)

            if valor == paciente.get("porte", "Médio"):
                radio.setChecked(True)

    def _criar_campo(self, titulo: str, valor: str) -> QLineEdit:
        rotulo = QLabel(titulo)
        rotulo.setObjectName("rotulo_campo")
        self.layout_conteudo.addWidget(rotulo)

        campo = QLineEdit()
        campo.setText(valor)
        self.layout_conteudo.addWidget(campo)

        return campo

    def validar(self) -> bool:
        if not self.nome_input.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome.")
            return False

        if self.especie_combo.currentIndex() == -1:
            QMessageBox.warning(self,"Campo obrigatório","Selecione a espécie.")
            return False

        if not self.idade_input.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe a idade.")
            return False

        return True

    def dados(self) -> dict:
        porte = self.porte_group.checkedButton()

        return {
            "nome": self.nome_input.text().strip(),
            "especie": self.especie_combo.currentText(),
            "idade": int(self.idade_input.text()),
            "porte": porte.property("valor") if porte else "Médio",
        }

    def _criar_seletor(self,titulo: str,opcoes: list[str],valor_atual: str) -> QComboBox:
        rotulo = QLabel(titulo)
        rotulo.setObjectName("rotulo_campo")
        self.layout_conteudo.addWidget(rotulo)

        seletor = QComboBox()
        seletor.addItems(opcoes)

        indice = seletor.findText(valor_atual)
        if indice >= 0:
            seletor.setCurrentIndex(indice)

        self.layout_conteudo.addWidget(seletor)

        return seletor