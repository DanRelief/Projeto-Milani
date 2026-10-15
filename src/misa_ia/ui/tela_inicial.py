from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import QCategoryAxis, QChart, QChartView, QSplineSeries, QValueAxis

from ..simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog

from .cadastrar_animal import DialogCadastrarAnimal
from .selecionar_animal import DialogSelecionarAnimal


class TelaInicial(QMainWindow):
    def __init__(self, usuario: dict) -> None:
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(1024, 720)
        self.setMinimumSize(900, 650)

        # 1. Inicialmente sem animal selecionado (dados zerados)
        self.paciente = {
            "nome": "---",
            "especie": "---",
            "idade": 0,
            "porte": "---",
            "medico_procedimento": "---",
            "procedimento": "Nenhum procedimento selecionado",
            "medico_medicacao": "---",
            "ultima_medicacao": "---",
            "quantidade_medicacao": "---",
            "estado_clinico": "---",
        }

        self.historico = []

        # Inicializa o simulador de sinais vitais
        self.simulator = SinalVitalSimulacao(self)
        self.simulator.measurement_generated.connect(self.update_chart)

        # Widget Central e Layout Principal
        central = QWidget()
        central.setObjectName("layout_fundo")
        layout_fundo = QVBoxLayout(central)
        layout_fundo.setContentsMargins(0, 0, 0, 0)
        layout_fundo.setSpacing(0)

        # Cabeçalho Limpo (Apenas logo, usuário, professor e menu)
        cabecalho = QWidget()
        cabecalho.setObjectName("cabecalho")
        cabecalho.setFixedHeight(75)
        layout_cabecalho = QHBoxLayout(cabecalho)
        layout_cabecalho.setContentsMargins(16, 0, 16, 0)
        layout_cabecalho.setSpacing(16)

        caminho_logo = Path(__file__).resolve().parents[3] / "assets" / "logo_misa.png"

        logo = QLabel()
        if caminho_logo.exists():
            imagem_logo = QPixmap(str(caminho_logo))
            logo.setPixmap(
                imagem_logo.scaled(
                    200,
                    70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        dados_usuario = QLabel(
            f'<span style="color:#08b9df;"><b>{usuario.get("role", "Aluno")}:</b></span> '
            f'{usuario.get("name", "")}<br>'
            f'<span style="color:#08b9df;"><b>{usuario.get("identifier_label", "RA")}:</b></span> '
            f'{usuario.get("identifier", "")}'
        )

        nome_professor = usuario.get("professor_name", "Milani")
        dados_professor = QLabel(
            f'<span style="color:#08b9df;"><b>Professor:</b></span> {nome_professor}'
        )

        botao_menu = QPushButton("☰")
        botao_menu.setObjectName("botao_menu")

        titulo = QLabel("M.I.S.A")
        titulo.setStyleSheet("font-size: 38px; font-weight: bold; color: #08b9df;")

        layout_cabecalho.addWidget(logo)
        layout_cabecalho.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout_cabecalho.addWidget(dados_usuario, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout_cabecalho.addStretch()
        layout_cabecalho.addWidget(dados_professor, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout_cabecalho.addWidget(botao_menu, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout_fundo.addWidget(cabecalho)

        # Conteúdo Principal
        conteudo_widget = self.montar_conteudo()
        layout_fundo.addWidget(conteudo_widget, 1)

        self._aplicar_estilos()
        self.setCentralWidget(central)
        self.simulator.start()

    def montar_conteudo(self) -> QWidget:
        conteudo = QWidget()
        grade = QGridLayout(conteudo)
        grade.setContentsMargins(18, 15, 18, 15)
        grade.setHorizontalSpacing(20)
        grade.setVerticalSpacing(10)

        card_paciente = self.criar_card_paciente()
        card_monitoramento = self.criar_card_monitoramento()
        card_historico = self.criar_card_historico()
        card_alertas = self.criar_card_alerta_ia()

        card_paciente.setFixedHeight(340)
        card_historico.setFixedHeight(240)
        card_monitoramento.setFixedHeight(420)
        card_alertas.setFixedHeight(140)

        coluna_esquerda = QVBoxLayout()
        coluna_direita = QVBoxLayout()

        coluna_esquerda.addWidget(self.criar_secao_card("INFORMAÇÕES DO PACIENTE", card_paciente))
        coluna_esquerda.addWidget(self.criar_secao_card("HISTÓRICO", card_historico))

        coluna_direita.addWidget(self.criar_secao_card("MONITORAMENTO EM TEMPO REAL", card_monitoramento))
        coluna_direita.addWidget(self.criar_secao_card("ALERTAS DE IA", card_alertas))

        coluna_esquerda.setAlignment(Qt.AlignmentFlag.AlignTop)
        coluna_direita.setAlignment(Qt.AlignmentFlag.AlignTop)

        grade.addLayout(coluna_esquerda, 0, 0)
        grade.addLayout(coluna_direita, 0, 1)
        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(1, 2)

        return conteudo

    def criar_card_paciente(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Informações do Paciente (inicialmente vazias)
        self.informacoes_paciente = QLabel()
        self.informacoes_paciente.setObjectName("informacoes_paciente")
        self.informacoes_paciente.setTextFormat(Qt.TextFormat.RichText)
        self.informacoes_paciente.setStyleSheet("font-size: 14px;")
        self.atualizar_informacoes_paciente()

        linha_informacoes = QHBoxLayout()
        linha_informacoes.setContentsMargins(0, 0, 0, 0)
        linha_informacoes.addWidget(self.informacoes_paciente, 1)

        self.btn_editar_paciente = QPushButton("Editar")
        self.btn_editar_paciente.setObjectName("botao_acao")
        self.btn_editar_paciente.setEnabled(False) # Desabilitado até carregar um paciente
        self.btn_editar_paciente.clicked.connect(self.editar_paciente)
        linha_informacoes.addWidget(
            self.btn_editar_paciente,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        layout.addLayout(linha_informacoes)

        # Seção CADASTRAR/MONITORAR
        cadastrar_label = QLabel("AÇÕES DO ANIMAL")
        cadastrar_label.setObjectName("titulo_cadastrar")
        cadastrar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cadastrar_label)

        # Botões de Ação reposicionados dentro do Card de Paciente
        linha_botoes_animais = QHBoxLayout()
        self.btn_cadastrar = QPushButton("Cadastrar Animal")
        self.btn_cadastrar.setObjectName("btn_card_animal")
        self.btn_cadastrar.clicked.connect(self._abrir_cadastro_animal)

        self.btn_monitorar = QPushButton("Monitorar Animal")
        self.btn_monitorar.setObjectName("btn_card_animal")
        self.btn_monitorar.clicked.connect(self._abrir_selecao_animal)

        linha_botoes_animais.addStretch()
        linha_botoes_animais.addWidget(self.btn_cadastrar)
        linha_botoes_animais.addWidget(self.btn_monitorar)
        linha_botoes_animais.addStretch()

        layout.addLayout(linha_botoes_animais)

        # Botões extras de lançamento de procedimento/medicação
        linha_cadastro_eventos = QHBoxLayout()
        procedimento = QPushButton("Procedimento")
        procedimento.clicked.connect(self.cadastrar_procedimento)

        medicacao = QPushButton("Medicação")
        medicacao.clicked.connect(self.cadastrar_medicacao)

        linha_cadastro_eventos.addStretch()
        linha_cadastro_eventos.addWidget(procedimento)
        linha_cadastro_eventos.addWidget(medicacao)
        linha_cadastro_eventos.addStretch()

        layout.addLayout(linha_cadastro_eventos)

        return card

    def _abrir_cadastro_animal(self) -> None:
        dlg = DialogCadastrarAnimal(self.usuario, self)
        dlg.exec()

    def _abrir_selecao_animal(self) -> None:
        dlg = DialogSelecionarAnimal(self.usuario, self)
        dlg.animal_selecionado.connect(self._carregar_animal_para_monitoramento)
        dlg.exec()

    def _carregar_animal_para_monitoramento(self, animal: dict, e_proprietario: bool) -> None:
        self.paciente["nome"] = animal["nome"]
        self.paciente["especie"] = animal["especie"]
        self.paciente["idade"] = animal["idade"]
        self.paciente["porte"] = animal["porte"].capitalize()
        self.paciente["procedimento"] = animal["procedimento"]
        self.paciente["estado_clinico"] = animal["estado_clinico"].capitalize()
        self.paciente["ultima_medicacao"] = animal.get("ultima_medicacao") or "Nenhuma"
        self.paciente["quantidade_medicacao"] = animal.get("quantidade") or "N/A"
        self.paciente["medico_procedimento"] = animal.get("nome_responsavel", "Desconhecido")

        self.atualizar_informacoes_paciente()

        pode_editar = e_proprietario or (self.usuario.get("role") == "Docente")
        self.btn_editar_paciente.setEnabled(pode_editar)

        if not pode_editar:
            QMessageBox.information(
                self,
                "Modo Somente Leitura",
                f"Você está monitorando o paciente de {animal.get('nome_responsavel', 'outro usuário')}. "
                "Alterações nos dados estão desabilitadas.",
            )

    def atualizar_informacoes_paciente(self) -> None:
        self.informacoes_paciente.setText(
            f"<span style='color:#08b9df'><b>Nome:</b></span> {self.paciente['nome']}<br>"
            f"<span style='color:#08b9df'><b>Espécie:</b></span> {self.paciente['especie']}<br>"
            f"<span style='color:#08b9df'><b>Idade:</b></span> {self.paciente['idade']} anos<br>"
            f"<span style='color:#08b9df'><b>Porte:</b></span> {self.paciente['porte']}<br><br>"
            f"<span style='color:#08b9df'><b>Responsável:</b></span> {self.paciente['medico_procedimento']}<br>"
            f"<span style='color:#08b9df'><b>Procedimento:</b></span> {self.paciente['procedimento']}<br>"
            f"<span style='color:#08b9df'><b>Estado Clínico:</b></span> {self.paciente['estado_clinico']}<br>"
            f"<span style='color:#08b9df'><b>Última Medicação:</b></span> {self.paciente['ultima_medicacao']} "
            f"&nbsp;&nbsp;<b>Qtd:</b> {self.paciente['quantidade_medicacao']}"
        )

    def criar_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return card

    def criar_secao_card(self, titulo: str, card: QFrame) -> QWidget:
        secao = QWidget()
        layout_secao = QVBoxLayout(secao)
        layout_secao.setContentsMargins(0, 0, 0, 0)
        layout_secao.setSpacing(4)
        layout_secao.setAlignment(Qt.AlignmentFlag.AlignTop)

        if titulo:
            titulo_label = QLabel(titulo)
            titulo_label.setObjectName("titulo_secao")
            layout_secao.addWidget(titulo_label)

        layout_secao.addWidget(card)
        return secao

    def criar_card_alerta_ia(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)

        alerta = QLabel(
            "Selecione ou cadastre um animal para visualizar as análises em tempo real e alertas da IA."
        )
        alerta.setTextFormat(Qt.TextFormat.RichText)
        alerta.setWordWrap(True)
        layout.addWidget(alerta)
        return card

    def criar_card_historico(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)

        self.historico_label = QLabel()
        self.historico_label.setTextFormat(Qt.TextFormat.RichText)
        self.historico_label.setWordWrap(True)
        self.atualizar_card_historico()

        layout.addWidget(self.historico_label)

        ver_mais = QPushButton("Ver Mais")
        ver_mais.setObjectName("botao_ver_mais")
        ver_mais.clicked.connect(self.ver_historico_completo)
        layout.addWidget(ver_mais, alignment=Qt.AlignmentFlag.AlignRight)

        return card

    def criar_card_monitoramento(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        self.grafico = QChart()
        self.grafico.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.grafico_view = QChartView(self.grafico)
        self.grafico_view.setFrameShape(QFrame.Shape.NoFrame)
        self.grafico_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout.addWidget(self.grafico_view, 1)

        self.oxigenio_serie = QSplineSeries()
        self.oxigenio_serie.setName("Oxigênio")

        self.batimentos_serie = QSplineSeries()
        self.batimentos_serie.setName("Batimento Cardíaco")

        self.pressao_serie = QSplineSeries()
        self.pressao_serie.setName("Pressão Arterial")

        self.grafico.addSeries(self.oxigenio_serie)
        self.grafico.addSeries(self.batimentos_serie)
        self.grafico.addSeries(self.pressao_serie)

        self.axis_x = QCategoryAxis()
        self.axis_x.setTitleText("Horário")

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 120)
        self.axis_y.setTitleText("Valor")

        self.grafico.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.grafico.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        for series in (
            self.oxigenio_serie,
            self.batimentos_serie,
            self.pressao_serie,
        ):
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        return card

    def editar_paciente(self) -> None:
        if self.paciente["nome"] == "---":
            QMessageBox.warning(self, "Aviso", "Selecione um animal antes de editar.")
            return

        self.popup_editar_paciente = EditarPacienteDialog(self.paciente, self)
        if self.popup_editar_paciente.exec() == QDialog.DialogCode.Accepted:
            self.paciente.update(self.popup_editar_paciente.dados())
            self.atualizar_informacoes_paciente()

    def cadastrar_procedimento(self) -> None:
        if self.paciente["nome"] == "---":
            QMessageBox.warning(self, "Aviso", "Selecione um animal para lançar procedimentos.")
            return

        dialogo = CadastrarProcedimentoDialog(self.paciente, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()
            self.historico.insert(0, dados)
            self.paciente["procedimento"] = dados["procedimento"]
            self.paciente["medico_procedimento"] = dados["medico_procedimento"]
            self.atualizar_informacoes_paciente()
            self.atualizar_card_historico()

    def cadastrar_medicacao(self) -> None:
        if self.paciente["nome"] == "---":
            QMessageBox.warning(self, "Aviso", "Selecione um animal para lançar medicações.")
            return

        dialogo = CadastrarMedicacaoDialog(self.paciente, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()
            self.historico.insert(0, dados)
            self.paciente["ultima_medicacao"] = dados["medicacao"]
            self.paciente["quantidade_medicacao"] = f"{dados['quantidade']} {dados['unidade']}"
            self.atualizar_informacoes_paciente()
            self.atualizar_card_historico()

    def ver_historico_completo(self) -> None:
        dialogo = HistoricoDialog(self.historico, self)
        dialogo.exec()

    def update_chart(self, medicao) -> None:
        index = self.oxigenio_serie.count()
        horario = medicao.tempomedicao.strftime("%H:%M")

        self.oxigenio_serie.append(index, medicao.oxigenio)
        self.batimentos_serie.append(index, medicao.batimento_cardiaco)
        self.pressao_serie.append(index, medicao.pressao_arterial)

        self.oxigenio_serie.setPointsVisible(True)
        self.batimentos_serie.setPointsVisible(True)
        self.pressao_serie.setPointsVisible(True)

        self.axis_x.append(horario, index + 1)
        self.axis_x.setRange(0, max(1, index + 1))

        if self.oxigenio_serie.count() > 24:
            self.oxigenio_serie.remove(0)
            self.batimentos_serie.remove(0)
            self.pressao_serie.remove(0)

    def atualizar_card_historico(self) -> None:
        if not self.historico:
            self.historico_label.setText("Nenhum procedimento ou medicação cadastrada.")
            return

        textos = []
        for registro in self.historico[:2]:
            if registro.get("tipo") == "Procedimento":
                textos.append(
                    f"Procedimento: {registro['procedimento']}<br>"
                    f"Médico responsável: {registro['medico_procedimento']}<br>"
                    f"Data: {registro.get('data', '')} Hora: {registro.get('hora', '')}<br><br>"
                )
            else:
                textos.append(
                    f"Responsável: {registro.get('medico_medicacao', '')}<br>"
                    f"Medicação: {registro.get('medicacao', '')} Qtd: {registro.get('quantidade', '')} {registro.get('unidade', '')}<br>"
                    f"Data: {registro.get('data', '')} Hora: {registro.get('hora', '')}<br><br>"
                )

        self.historico_label.setText("".join(textos))

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            #cabecalho { background-color: white; border-bottom: 2px solid #e0e0e0; }
            #cabecalho QLabel { font-size: 14px; color: #555555; }
            #botao_menu {
                background-color: transparent;
                color: #08b9df;
                border: none;
                font-size: 26px;
                font-weight: bold;
            }
            #botao_menu:hover { color: #078eaa; }
            #layout_fundo { background-color: #08b9df; }
            #card {
                background-color: white;
                border: none;
                border-radius: 10px;
            }
            #titulo_secao {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            #card QLabel { color: black; font-size: 14px; }
            #card QLabel b { color: #08b9df; }
            #botao_ver_mais {
                color: #2100b8;
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
            #titulo_cadastrar {
                color: #2100b8;
                font-size: 14px;
                font-weight: bold;
            }
            #btn_card_animal {
                background-color: #287a55;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: 600;
                font-size: 12px;
            }
            #btn_card_animal:hover { background-color: #216746; }
            """
        )