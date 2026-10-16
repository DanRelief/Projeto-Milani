from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
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

from ..infrastructure.simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog

from .cadastrar_animal import DialogCadastrarAnimal
from .selecionar_animal import DialogSelecionarAnimal

class TelaInicial(QMainWindow):
    logout_requested = Signal()

    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(1024, 720)
        self.setminimoSize(900, 650)

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
        self.simulator = None

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

        caminho_logo = Path(__file__).resolve().parents[2] / "assets" / "logo_misa.png"

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

        # Botão do menu lateral
        botao_menu = QPushButton("\u2630")
        botao_menu.setObjectName("botao_menu")
        botao_menu.clicked.connect(self.alternar_menu)

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
        self.montar_menu_lateral(central, usuario)

    def montar_menu_lateral(
        self, central: QWidget, usuario: dict[str, str]
    ) -> None:
        """Cria o painel lateral sobreposto a tela inicial."""
        self.menu_overlay = QFrame(central)
        self.menu_overlay.setObjectName("menu_overlay")
        self.menu_overlay.hide()
        self.menu_opacidade = QGraphicsOpacityEffect(self.menu_overlay)
        self.menu_opacidade.setOpacity(0.0)
        self.menu_overlay.setGraphicsEffect(self.menu_opacidade)
        self.menu_animacao = None
        self.menu_aberto = False

        self.menu_panel = QFrame(self.menu_overlay)
        self.menu_panel.setObjectName("menu_panel")

        layout = QVBoxLayout(self.menu_panel)
        layout.setContentsMargins(20, 10, 20, 14)
        layout.setSpacing(8)

        fechar = QPushButton("\u2630")
        fechar.setObjectName("botao_fechar_menu")
        fechar.setToolTip("Fechar menu")
        fechar.clicked.connect(self.alternar_menu)
        layout.addWidget(fechar, alignment=Qt.AlignmentFlag.AlignTop)

        perfil = QPushButton("Perfil")
        perfil.setObjectName("item_menu")
        perfil.clicked.connect(lambda: self.abrir_perfil(usuario))
        layout.addWidget(perfil)

        sair = QPushButton("Sair")
        sair.setObjectName("item_menu")
        sair.clicked.connect(self.solicitar_saida)
        layout.addWidget(sair)

        baixar_relatorio = QPushButton("Baixar relatório do dia")
        baixar_relatorio.setObjectName("item_menu")
        baixar_relatorio.setToolTip("Em breve")
        layout.addWidget(baixar_relatorio)

        layout.addStretch()

        caminho_logo = Path(__file__).resolve().parents[2] / "assets" / "logo_misa.png"
        logo_menu = QLabel()
        imagem_logo = QPixmap(str(caminho_logo))
        logo_menu.setPixmap(
            imagem_logo.scaled(
                160,
                135,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_menu)

        self.menu_overlay.setStyleSheet(
            """
            QFrame#menu_overlay {
                background-color: rgba(0, 0, 0, 155);
            }

            QFrame#menu_panel {
                background-color: white;
                border-radius: 16px;
            }

            QPushButton#botao_fechar_menu {
                background-color: #2100b8;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 6px 18px;
                min-height: 32px;
                font-size: 25px;
                font-weight: bold;
            }

            QPushButton#botao_fechar_menu:hover {
                background-color: #351bc9;
            }

            QPushButton#botao_fechar_menu:pressed {
                background-color: #180087;
            }

            QPushButton#item_menu {
                color: #08b9df;
                background-color: transparent;
                border: none;
                padding: 4px 10px;
                font-size: 20px;
                font-weight: bold;
                text-align: left;
            }

            QPushButton#item_menu:hover {
                color: #078eaa;
            }
            """
        )
        self.atualizar_geometria_menu()

    def atualizar_geometria_menu(self) -> None:
        """Mantem o painel alinhado a direita quando a janela muda de tamanho."""
        if not hasattr(self, "menu_overlay"):
            return

        area = self.centralWidget().rect()
        self.menu_overlay.setGeometry(area)

        largura = min(360, max(0, area.width() - 20))
        self.menu_panel.setGeometry(
            area.width() - largura,
            10,
            largura,
            max(0, area.height() - 20),
        )

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self.atualizar_geometria_menu()

    def alternar_menu(self) -> None:
        if self.menu_animacao is not None:
            self.menu_animacao.stop()
            self.menu_animacao = None

        if self.menu_aberto:
            self.fechar_menu()
        else:
            self.abrir_menu()

    def abrir_menu(self) -> None:
        self.atualizar_geometria_menu()
        area = self.centralWidget().rect()
        largura = self.menu_panel.width()
        destino = self.menu_panel.geometry()
        inicio = QRect(area.width(), destino.y(), largura, destino.height())

        if not self.menu_overlay.isVisible():
            self.menu_panel.setGeometry(inicio)
            self.menu_opacidade.setOpacity(0.0)
            self.menu_overlay.show()

        self.menu_overlay.raise_()
        self.menu_panel.raise_()
        self.menu_aberto = True
        self.animar_menu(destino, 1.0)

    def fechar_menu(self) -> None:
        area = self.centralWidget().rect()
        atual = self.menu_panel.geometry()
        destino = QRect(
            area.width(),
            atual.y(),
            atual.width(),
            atual.height(),
        )

        self.menu_aberto = False
        self.animar_menu(destino, 0.0)

    def animar_menu(self, destino: QRect, opacidade_final: float) -> None:
        animacao_geometria = QPropertyAnimation(self.menu_panel, b"geometry", self)
        animacao_geometria.setDuration(280)
        animacao_geometria.setStartValue(self.menu_panel.geometry())
        animacao_geometria.setEndValue(destino)
        animacao_geometria.setEasingCurve(QEasingCurve.Type.OutCubic)

        animacao_opacidade = QPropertyAnimation(
            self.menu_opacidade, b"opacity", self
        )
        animacao_opacidade.setDuration(280)
        animacao_opacidade.setStartValue(self.menu_opacidade.opacity())
        animacao_opacidade.setEndValue(opacidade_final)
        animacao_opacidade.setEasingCurve(QEasingCurve.Type.OutCubic)

        grupo = QParallelAnimationGroup(self)
        grupo.addAnimation(animacao_geometria)
        grupo.addAnimation(animacao_opacidade)
        grupo.finished.connect(lambda: self.finalizar_animacao_menu(grupo))
        self.menu_animacao = grupo
        grupo.start()

    def finalizar_animacao_menu(self, grupo) -> None:
        if self.menu_animacao is not grupo:
            return

        self.menu_animacao = None
        if self.menu_aberto:
            self.menu_opacidade.setOpacity(1.0)
            return

        self.menu_opacidade.setOpacity(0.0)
        self.menu_overlay.hide()

    def abrir_perfil(self, usuario: dict[str, str]) -> None:
        self.menu_overlay.hide()
        QMessageBox.information(
            self,
            "Perfil",
            f"Nome: {usuario['name']}\n"
            f"{usuario['identifier_label']}: {usuario['identifier']}\n"
            f"Perfil: {usuario['role']}",
        )

    def solicitar_saida(self) -> None:
        self.menu_overlay.hide()
        self.logout_requested.emit()

    def closeEvent(self, evento) -> None:
        if self.simulator is not None:
            self.simulator.stop()
        super().closeEvent(evento)

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
        layout.setSpacing(6)
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
        self.btn_editar_paciente.setEnabled(False)  # Desabilitado até carregar um paciente
        self.btn_editar_paciente.clicked.connect(self.editar_paciente)
        linha_informacoes.addWidget(
            self.btn_editar_paciente,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        layout.addLayout(linha_informacoes)

        # Seção AÇÕES DO ANIMAL
        cadastrar_label = QLabel("AÇÕES DO ANIMAL")
        cadastrar_label.setObjectName("titulo_cadastrar")
        cadastrar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cadastrar_label)

        # 1. Linha com os botões de Gestão do Animal (Cadastrar / Monitorar)
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

        # 2. Linha com os botões de Lançamentos Clínicos (Procedimento / Medicação)
        linha_cadastro_eventos = QHBoxLayout()
        btn_procedimento = QPushButton("Procedimento")
        btn_procedimento.setObjectName("btn_card_animal")
        btn_procedimento.clicked.connect(self.cadastrar_procedimento)

        btn_medicacao = QPushButton("Medicação")
        btn_medicacao.setObjectName("btn_card_animal")
        btn_medicacao.clicked.connect(self.cadastrar_medicacao)

        linha_cadastro_eventos.addStretch()
        linha_cadastro_eventos.addWidget(btn_procedimento)
        linha_cadastro_eventos.addWidget(btn_medicacao)
        linha_cadastro_eventos.addStretch()

        layout.addLayout(linha_cadastro_eventos)

        return card

# Dentro da classe TelaInicial:

    def criar_card_monitoramento(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        self.grafico = QChart()
        self.grafico.setTitle("Sinais Vitais e Agentes Inalatórios")
        self.grafico.setAnimationOptions(QChart.AnimationOption.NoAnimation) # Animação desativada para plotagem contínua fluida

        self.grafico_view = QChartView(self.grafico)
        self.grafico_view.setFrameShape(QFrame.Shape.NoFrame)
        self.grafico_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.grafico_view, 1)

        # Mapeamento e estilo das 8 séries de dados (Cor distinta para cada parâmetro)
        self.series_map = {
            "freq_cardiaca": (QSplineSeries(), "FC (bpm)", QColor("#E74C3C")),         # Vermelho
            "pressao_arterial": (QSplineSeries(), "PA (mmHg)", QColor("#E67E22")),     # Laranja
            "spo2": (QSplineSeries(), "SpO2 (%)", QColor("#2ECC71")),                  # Verde
            "etco2": (QSplineSeries(), "ETCO2 (mmHg)", QColor("#F1C40F")),             # Amarelo
            "freq_respiratoria": (QSplineSeries(), "FR (rpm)", QColor("#3498DB")),     # Azul Claro
            "temperatura": (QSplineSeries(), "Temp (°C)", QColor("#9B59B6")),          # Roxo
            "fluxo_o2_ar": (QSplineSeries(), "O2/Ar (L/min)", QColor("#1ABC9C")),      # Turquesa
            "iso_sevo": (QSplineSeries(), "Iso/Sevo (%)", QColor("#34495E"))           # Cinza Escuro
        }

        for key, (series, label, color) in self.series_map.items():
            series.setName(label)
            pen = QPen(color)
            pen.setWidth(2)
            series.setPen(pen)
            self.grafico.addSeries(series)

        # Configuração dos Eixos
        self.axis_x = QCategoryAxis()
        self.axis_x.setTitleText("Horário Decorrido")

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 180) # Amplitude abrangendo os principais sinais vitais
        self.axis_y.setTitleText("Valor")

        self.grafico.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.grafico.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        for series, _, _ in self.series_map.values():
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        return card

    def update_chart(self, medicao) -> None:
        if not medicao:
            return
        serie_referencia = self.series_map["spo2"][0]
        index = serie_referencia.count()
        horario = medicao[0].data_hora.strftime("%H:%M:%S")

        # Dicionário dinâmico com fallback seguro (pega do atributo da medição ou usa 0.0)
        mapa_series = {
        "spo2": "spo2",
        "temperature": "temperatura",
        "media_arterial_pressure": "pressao_arterial",
        }

        for medicoes in medicao:
            chave = mapa_series.get(medicoes.parametro.value)

            if chave is None:
                continue

            self.series_map[chave][0].append(
                index,
                float(medicoes.value),
            )

        self.axis_x.append(horario, index + 1)

        JANELA_VISIVEL = 30

        if index >= JANELA_VISIVEL:
            self.axis_x.setRange(
                index - JANELA_VISIVEL + 1,
                index + 1,
            )
        else:
            self.axis_x.setRange(
                0,
                max(1, index + 1),
            )

        primeira_serie = self.series_map["spo2"][0]
        
        # Limpeza de buffer de memória para séries muito longas
        BUFFER_MAXIMO = 120
        if primeira_serie.count() > BUFFER_MAXIMO:
            for series, _, _ in self.series_map.values():
                series.remove(0)

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
        if self.simulator is not None:
            self.simulator.stop()

        id_paciente = str(animal["id"])
        id_sessao = str(uuid4())

        self.simulator = SinalVitalSimulacao(
            id_paciente=id_paciente,
            id_sessao=id_sessao,
            parent=self,
        )

        self.simulator.measurement_generated.connect(self.update_chart)
        self.simulator.start()

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
