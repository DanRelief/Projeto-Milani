from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout,QLabel,QMainWindow,QPushButton,QVBoxLayout,QWidget,QFrame,QGridLayout,QSizePolicy,QMessageBox
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis, QSplineSeries
from ..simulation.sinais_vitais_simulacao import SinalVitalSimulacao


class TelaInicial(QMainWindow):
    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)
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
        botao_menu = QPushButton("☰")
        botao_menu.setObjectName("botao_menu")

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
                font-size: 32px;
                font-weight: bold;
            }

            #botao_menu:hover {
                color: #078eaa;
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

        #botao_acao {
        background-color: #2100b8;
        color: white;
        border: none;
        border-radius: 22px;
        padding: 6px 18px;
        min-height: 32px;
        font-size: 16px;
    }

        #botao_acao:hover {
        background-color: #351bc9;
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
        self.simulator.start()

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

        informacoes = QLabel(
            "<span style='color:#08b9df'><b>Nome:</b></span> Beto<br>"
            "<span style='color:#08b9df'><b>Espécie:</b></span> Cachorro<br>"
            "<span style='color:#08b9df'><b>Idade:</b></span> 7 anos<br>"
            "<span style='color:#08b9df'><b>Porte:</b></span> Médio<br><br>"
            "<span style='color:#08b9df'><b>Médico Responsável:</b></span> Dr. Rafael<br>"
            "<span style='color:#08b9df'><b>Procedimento:</b></span> Cirurgia de Pedra no Rim<br>"
            "<span style='color:#08b9df'><b>Estado Clínico:</b></span> Estável<br>"
            "<span style='color:#08b9df'><b>Última Medicação:</b></span> Propofol"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "<span style='color:#08b9df'><b>Qtd:</b></span> 15 mg"
        )
        informacoes.setObjectName("informacoes_paciente")
        informacoes.setTextFormat(Qt.TextFormat.RichText)
        informacoes.setStyleSheet("font-size: 20px;")

        informacoes.setWordWrap(False)

        linha_informacoes = QHBoxLayout()
        linha_informacoes.setContentsMargins(0, 0, 0, 0)
        linha_informacoes.setSpacing(8)
        linha_informacoes.addWidget(informacoes, 1)

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

        historico = QLabel(
        "Medicação: Paracetamol                 Qtd: 0.5mg<br>"
        "data: 03/09/2026 - hora: 19:30h<br><br>"
        "Procedimento: Cirurgia de Pele       "
        "Médico Responsável: Dr. Rafael<br>"
        "data: 03/09/2026 - hora: 20:30h"
    )

        historico.setTextFormat(Qt.TextFormat.RichText)
        historico.setWordWrap(True)
        layout.addWidget(historico)

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
        QMessageBox.information(self, "Editar Paciente", "Função de edição de paciente não implementada.")

    def cadastrar_procedimento(self) -> None:
        QMessageBox.information(
            self,
            "Procedimento",
            "Aqui será aberto o cadastro de procedimento.",
        )

    def cadastrar_medicacao(self) -> None:
        QMessageBox.information(
            self,
            "Medicação",
            "Aqui será aberto o cadastro de medicação.",
        )

    def ver_historico_completo(self) -> None:
        QMessageBox.information(
            self,
            "Histórico",
            "Aqui será exibido o histórico completo.",
        )

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