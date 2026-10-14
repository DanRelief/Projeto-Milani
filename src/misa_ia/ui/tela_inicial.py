from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis, QSplineSeries
from ..simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog


class TelaInicial(QMainWindow):
    logout_requested = Signal()

    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        self.paciente = {
            "nome": "Beto",
            "especie": "Cachorro",
            "idade": 7,
            "porte": "Médio",
            "medico_procedimento": "Dr. Rafael",
            "procedimento": "Cirurgia de Pedra no Rim",
            "medico_medicacao": "Dra. Ana",
            "ultima_medicacao": "Propofol",
            "quantidade_medicacao": "15 mg",
            "estado_clinico": "Estável",
        }

        self.historico = []

        self.simulator = SinalVitalSimulacao(self)
        self.simulator.measurement_generated.connect(self.update_chart)

        central = QWidget()
        central.setObjectName("layout_fundo")
        layout_fundo = QVBoxLayout(central)
        layout_fundo.setContentsMargins(0, 0, 0, 0)
        layout_fundo.setSpacing(0)

        cabecalho = QWidget()
        cabecalho.setObjectName("cabecalho")
        cabecalho.setFixedHeight(75)
        layout_cabecalho = QHBoxLayout(cabecalho)
        layout_cabecalho.setContentsMargins(16, 0, 16, 0)
        layout_cabecalho.setSpacing(24)

        caminho_logo = Path(__file__).resolve().parents[3] / "assets" / "logo_misa.png"

        logo = QLabel()
        imagem_logo = QPixmap(str(caminho_logo))
        logo.setPixmap(
            imagem_logo.scaled(
                240,
                85,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        dados_usuario = QLabel(
            f'<span style="color:#08b9df;"><b>{usuario["role"]}:</b></span> '
            f'{usuario["name"]}<br>'
            f'<span style="color:#08b9df;"><b>{usuario["identifier_label"]}:</b></span> '
            f'{usuario["identifier"]}'
        )

        nome_professor = usuario.get("professor_name", "Milani")
        dados_professor = QLabel(
            f'<span style="color:#08b9df;"><b>Professor:</b></span> '
            f'{nome_professor}'
        )

        # Botão do menu lateral
        botao_menu = QPushButton("\u2630")
        botao_menu.setObjectName("botao_menu")
        botao_menu.clicked.connect(self.alternar_menu)

        titulo = QLabel("M.I.S.A")
        titulo.setStyleSheet("font-size: 50px; font-weight: bold; color: #08b9df;")

        layout_cabecalho.addWidget(logo)
        layout_cabecalho.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignTop)
        layout_cabecalho.addWidget(dados_usuario)
        layout_cabecalho.addStretch()
        layout_cabecalho.addWidget(dados_professor)
        layout_cabecalho.addWidget(botao_menu)
        layout_cabecalho.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout_fundo.addWidget(cabecalho, alignment=Qt.AlignmentFlag.AlignTop)
        layout_fundo.addWidget(self.montar_conteudo())
        self.setStyleSheet(
            """
            #cabecalho {
                background-color: white;
            }

            #cabecalho QLabel {
                font-size: 20px;
                color: #aaaaaa;
            }

            #botao_menu {
                background-color: transparent;
                color: #08b9df;
                border: none;
                padding: 0;
                min-width: 0;
                max-width: none;
                min-height: 0;
                max-height: none;
                font-size: 32px;
                font-weight: bold;
            }

            #botao_menu:hover {
                color: #078eaa;
            }

            #botao_menu:pressed {
                color: #057d96;
            }

            #layout_fundo {
                background-color: #08b9df;
            }
            """
        )
        self.setStyleSheet(self.styleSheet() + """
        #card {
            background-color: white;
            border: none;
            border-radius: 10px;
        }

        #titulo_secao {
            color: white;
            font-size: 20px;
            font-weight: bold;
        }

        #card QLabel {
            color: black;
            font-size: 16px;
        }

        #card QLabel b {
            color: #08b9df;
        }

        #botao_ver_mais {
            color: #2100b8;
            background-color: transparent;
            border: none;
            font-size: 16px;
            font-weight: bold;
        }

        #titulo_cadastrar {
        color: #2100b8;
        font-size: 20px;
        font-weight: bold;
        }

    
        """
    )

        self.setCentralWidget(central)
        self.montar_menu_lateral(central, usuario)
        self.simulator.start()

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

        caminho_logo = Path(__file__).resolve().parents[3] / "assets" / "logo_misa.png"
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
        self.simulator.stop()
        super().closeEvent(evento)

    def montar_conteudo(self) -> QWidget:
        #Criar o widget principal da área abaixo do cabeçãlho, os cards e tudo mais

        conteudo = QWidget()
        grade = QGridLayout(conteudo)
        grade.setContentsMargins(22, 30, 22, 15)
        grade.setHorizontalSpacing(28)
        grade.setVerticalSpacing(10)

        card_paciente = self.criar_card_paciente()
        card_monitoramento = self.criar_card_monitoramento()
        card_historico = self.criar_card_historico()
        card_alertas = self.criar_card_alerta_ia()

        #tamanhos cards brancos, aqui tem os tamanhos deles de altura, mas a largura é automática, se ajusta ao tamanho da tela
        card_paciente.setFixedHeight(340)
        card_historico.setFixedHeight(260)

        card_monitoramento.setFixedHeight(450)
        card_alertas.setFixedHeight(150)
        

        coluna_esquerda = QVBoxLayout()
        coluna_direita = QVBoxLayout()

        coluna_esquerda.addWidget(self.criar_secao_card("INFORMAÇÕES DO PACIENTE",card_paciente))

        coluna_esquerda.addWidget(self.criar_secao_card("HISTÓRICO",card_historico))

        coluna_direita.addWidget(self.criar_secao_card("",card_monitoramento))

        coluna_direita.addWidget(self.criar_secao_card("ALERTAS DE IA",card_alertas))

        coluna_esquerda.setAlignment(Qt.AlignmentFlag.AlignTop)
        coluna_direita.setAlignment(Qt.AlignmentFlag.AlignTop)

        grade.addLayout(coluna_esquerda, 0, 0)
        grade.addLayout(coluna_direita, 0, 1)
        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(1, 2)

        return conteudo

    def criar_card(self) -> QFrame:
        #Cria o card branco visual
        card = QFrame()
        card.setObjectName("card")

        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return card

    def criar_secao_card(self, titulo: str, card: QFrame) -> QWidget:
        secao = QWidget()
        layout_secao = QVBoxLayout(secao)
        layout_secao.setContentsMargins(0, 0, 0, 0)
        layout_secao.setSpacing(1)
        layout_secao.setAlignment(Qt.AlignmentFlag.AlignTop)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        titulo_label.setObjectName("titulo_secao")
        titulo_label.setContentsMargins(0, 0, 0, 0)
        layout_secao.addWidget(titulo_label)
        layout_secao.addWidget(card)

        return secao

    def criar_card_paciente(self) -> QFrame:
        card = self.criar_card()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.informacoes_paciente = QLabel()
        self.informacoes_paciente.setObjectName("informacoes_paciente")
        self.informacoes_paciente.setTextFormat(Qt.TextFormat.RichText)
        self.informacoes_paciente.setStyleSheet("font-size: 20px;")
        self.informacoes_paciente.setWordWrap(False)
        self.atualizar_informacoes_paciente()

        linha_informacoes = QHBoxLayout()
        linha_informacoes.setContentsMargins(0, 0, 0, 0)
        linha_informacoes.setSpacing(8)
        linha_informacoes.addWidget(self.informacoes_paciente, 1)

        editar = QPushButton("Editar")
        editar.setObjectName("botao_acao")
        editar.clicked.connect(self.editar_paciente)
        linha_informacoes.addWidget(
            editar,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        layout.addLayout(linha_informacoes)

        cadastrar = QLabel("CADASTRAR")
        cadastrar.setObjectName("titulo_cadastrar")
        cadastrar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(cadastrar)

        linha_cadastro = QHBoxLayout()

        procedimento = QPushButton("Procedimento")
        procedimento.setObjectName("botao_acao")
        procedimento.clicked.connect(self.cadastrar_procedimento)

        medicacao = QPushButton("Medicação")
        medicacao.setObjectName("botao_acao")
        medicacao.clicked.connect(self.cadastrar_medicacao)

        linha_cadastro.addStretch()
        linha_cadastro.addWidget(procedimento)
        linha_cadastro.addWidget(medicacao)
        linha_cadastro.addStretch()

        layout.addLayout(linha_cadastro)

        return card

    def criar_card_alerta_ia(self) -> QFrame:
        card = self.criar_card()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 0, 14, 10)

        alerta  = QLabel(
        "Paciente em Estado estável do período das 10:15 às 10:35, "
        "não apresentando sinais de mudança ou estresse conforme os "
        "procedimentos feitos.<br><br>"
        "Fique atento à pressão arterial, aconteceu uma decaída "
        "abrupta às 10:30 mas que voltou a se estabilizar."
    )

        alerta.setTextFormat(Qt.TextFormat.RichText)
        alerta.setWordWrap(True)
        layout.addWidget(alerta)
        return card

    def criar_card_historico(self) -> QFrame:
        card = self.criar_card()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 0, 14, 10)

        self.historico_label = QLabel()
        self.historico_label.setWordWrap(True)

        self.atualizar_card_historico()

        self.historico_label.setTextFormat(Qt.TextFormat.RichText)
        self.historico_label.setWordWrap(True)
        layout.addWidget(self.historico_label)

        ver_mais = QPushButton("Ver Mais")
        ver_mais.setObjectName("botao_ver_mais")
        ver_mais.clicked.connect(self.ver_historico_completo)
        layout.addWidget(ver_mais, alignment=Qt.AlignmentFlag.AlignRight)

        return card
    
    def criar_card_monitoramento(self) -> QFrame:
        card = self.criar_card()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 0, 10, 10)

        self.grafico = QChart()
        self.grafico.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.grafico_view = QChartView(self.grafico)
        self.grafico_view.setFrameShape(QFrame.Shape.NoFrame)
        self.grafico_view.setStyleSheet("border: none; background-color: white;")

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
        self.popup_editar_paciente = EditarPacienteDialog(self.paciente, self)
        if self.popup_editar_paciente.exec() == QDialog.DialogCode.Accepted:
            self.paciente.update(self.popup_editar_paciente.dados())
            self.atualizar_informacoes_paciente()
            
    def cadastrar_procedimento(self) -> None:
        dialogo = CadastrarProcedimentoDialog(self.paciente, self)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            self.historico.insert(0, dados)

            self.paciente["procedimento"] = dados["procedimento"]
            self.paciente["medico_procedimento"] = (
                dados["medico_procedimento"]
            )

            self.atualizar_informacoes_paciente()
            self.atualizar_card_historico()

    def cadastrar_medicacao(self) -> None:
        dialogo = CadastrarMedicacaoDialog(self.paciente, self)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            self.historico.insert(0, dados)

            self.paciente["ultima_medicacao"] = dados["medicacao"]
            self.paciente["quantidade_medicacao"] = (
                f"{dados['quantidade']} {dados['unidade']}"
            )

            self.atualizar_informacoes_paciente()
            self.atualizar_card_historico()

    def ver_historico_completo(self) -> None:
        dialogo = HistoricoDialog(self.historico,self)
        dialogo.exec()

    def update_chart(self, medicao):
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

        # Mantém somente as últimas 24 medições, equivalentes a 2 horas.
        if self.oxigenio_serie.count() > 24:
            self.oxigenio_serie.remove(0)
            self.batimentos_serie.remove(0)
            self.pressao_serie.remove(0)

    def atualizar_informacoes_paciente(self) -> None:
        self.informacoes_paciente.setText(
            f"<span style='color:#08b9df'><b>Nome:</b></span> "
            f"{self.paciente['nome']}<br>"
            f"<span style='color:#08b9df'><b>Espécie:</b></span> "
            f"{self.paciente['especie']}<br>"
            f"<span style='color:#08b9df'><b>Idade:</b></span> "
            f"{self.paciente['idade']} anos<br>"
            f"<span style='color:#08b9df'><b>Porte:</b></span> "
            f"{self.paciente['porte']}<br><br>"
            f"<span style='color:#08b9df'><b>Responsável pela aplicação:</b></span> "
            f"{self.paciente['medico_procedimento']}<br>"
            f"<span style='color:#08b9df'><b>Procedimento:</b></span> "
            f"{self.paciente['procedimento']}<br>"
            f"<span style='color:#08b9df'><b>Estado Clínico:</b></span> "
            f"{self.paciente['estado_clinico']}<br>"
            f"<span style='color:#08b9df'><b>Última Medicação:</b></span> "
            f"{self.paciente['ultima_medicacao']}"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"<span style='color:#08b9df'><b>Qtd:</b></span> "
            f"{self.paciente['quantidade_medicacao']}"
        )

    def atualizar_card_historico(self) -> None:
        if not self.historico:
            self.historico_label.setText(
                "Nenhum procedimento ou medicação cadastrada."
            )
            return

        textos = []

        for registro in self.historico[:2]:
            if registro["tipo"] == "Procedimento":
                textos.append(
                    f"Procedimento: {registro['procedimento']}<br>"
                    f"Médico responsável: "
                    f"{registro['medico_procedimento']}<br>"
                    f"data: {registro['data']} - "
                    f"hora: {registro['hora']}<br><br>"
                )
            else:
                textos.append(
                    f"Responsável: "
                    f"{registro['medico_medicacao']}<br>"
                    f"Medicação: {registro['medicacao']} "
                    f"Qtd: {registro['quantidade']} "
                    f"{registro['unidade']}<br>"
                    f"data: {registro['data']} - "
                    f"hora: {registro['hora']}<br><br>"
                )

        self.historico_label.setText("".join(textos))
