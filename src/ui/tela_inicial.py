from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
    QThread,
    QTimer,
)
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
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
    QGraphicsDropShadowEffect,
)
from PySide6.QtCharts import QCategoryAxis, QChart, QChartView, QLineSeries, QValueAxis

from infrastructure.repositories.repositorio_sessoes import RepositorioSessoes

from ..infrastructure.simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog

from .cadastrar_animal import DialogCadastrarAnimal
from .selecionar_animal import DialogSelecionarAnimal
from ..application.monitoramento.controlador_monitoramento import ControladorMonitoramento
from ..domain.measurement import ParametroVital
from datetime import datetime
from src.infrastructure.repositories.repositorio_medicacoes import RepositorioMedicacoes
from src.infrastructure.repositories.repositorio_procedimentos import RepositorioProcedimentos
from src.ia.llm.worker_relatorio import WorkerRelatorio

class TelaInicial(QMainWindow):
    logout_requested = Signal()

    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(1024, 720)
        self.setMinimumSize(900, 650)
        self.indice_grafico = 0
        self.parametro_grafico_selecionado = None
        self.id_sessao_atual = None
        self.repositorio_sessoes = RepositorioSessoes()
        self.repositorio_procedimentos = RepositorioProcedimentos()
        self.repositorio_medicacoes = RepositorioMedicacoes()
        self.thread_relatorio = None
        self.worker_relatorio = None
        self.relatorio_ia_atual = None
        self.analises_atuais = {}
        self.estado_alerta_atual = "normal"
        self.alerta_animacao_timer = QTimer(self)
        self.alerta_animacao_timer.timeout.connect(
            self._alternar_animacao_alerta
        )
        self.alerta_animacao_fase_forte = False
        self.sombra_alerta = None

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
        self.controlador_monitoramento = ControladorMonitoramento(parent=self)
        self.controlador_monitoramento.medicoes_atualizadas.connect(self.update_chart)

        self.controlador_monitoramento.spo2_atualizada.connect(self.atualizar_spo2)
        self.controlador_monitoramento.temperatura_atualizada.connect(self.atualizar_temperatura)
        self.controlador_monitoramento.pam_atualizada.connect(self.atualizar_pam)

        self.controlador_monitoramento.resumo_monitoramento_atualizado.connect(self.atualizar_resumo_monitoramento)

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

        self.sombra_alerta = QGraphicsDropShadowEffect(self.card_alerta_ia)
        self.sombra_alerta.setBlurRadius(20)
        self.sombra_alerta.setOffset(0, 0)
        self.sombra_alerta.setColor(QColor(255, 0, 0, 0))
        self.card_alerta_ia.setGraphicsEffect(self.sombra_alerta)

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

        self.btn_relatorio = QPushButton("Relatório com IA")
        self.btn_relatorio.setObjectName("item_menu")
        self.btn_relatorio.setToolTip("Gerar relatório do monitoramento")
        self.btn_relatorio.clicked.connect(self.gerar_relatorio)
        layout.addWidget(self.btn_relatorio)

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

        if self.id_sessao_atual is not None:

            try:
                self.repositorio_sessoes.encerrar_sessao(self.id_sessao_atual)

            except Exception as erro:
                print(
                    "[M.I.S.A] Erro ao encerrar "
                    f"sessão: {erro}"
                )

            self.id_sessao_atual = None

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
        card_historico.setFixedHeight(280)

        card_monitoramento.setMinimumHeight(380)
        card_alertas.setMinimumHeight(220)
        card_alertas.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding,)

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

        self.btn_simular_queda_spo2 = (
            QPushButton(
                "Queda SpO₂"
            )
        )

        self.btn_simular_queda_pam = (
            QPushButton(
                "Queda PAM"
            )
        )

        self.btn_simular_temperatura = (
            QPushButton(
                "Aumentar Temp."
            )
        )

        self.btn_restaurar_sinais = (
            QPushButton(
                "Restaurar"
            )
        )

        for botao in (
            self.btn_simular_queda_spo2,
            self.btn_simular_queda_pam,
            self.btn_simular_temperatura,
            self.btn_restaurar_sinais,
        ):
            botao.setObjectName(
                "btn_card_animal"
            )

        linha_cadastro_eventos.addStretch()
        linha_cadastro_eventos.addWidget(btn_procedimento)
        linha_cadastro_eventos.addWidget(btn_medicacao)
        linha_cadastro_eventos.addStretch()

        layout.addLayout(linha_cadastro_eventos)

        self.btn_simular_queda_spo2.clicked.connect(
        self.simular_queda_spo2
    )

        self.btn_simular_queda_pam.clicked.connect(
            self.simular_queda_pam
        )

        self.btn_simular_temperatura.clicked.connect(
            self.simular_aumento_temperatura
        )

        self.btn_restaurar_sinais.clicked.connect(
            self.restaurar_sinais_teste
        )

        linha_simulacao = QHBoxLayout()

        linha_simulacao.addStretch()

        linha_simulacao.addWidget(
            self.btn_simular_queda_spo2
        )

        linha_simulacao.addWidget(
            self.btn_simular_queda_pam
        )

        linha_simulacao.addWidget(
            self.btn_simular_temperatura
        )

        linha_simulacao.addWidget(
            self.btn_restaurar_sinais
        )

        linha_simulacao.addStretch()

        layout.addLayout(
            linha_simulacao
        )

        return card

# Dentro da classe TelaInicial:

    def criar_card_monitoramento(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        linha_valores = QHBoxLayout()

        self.valor_spo2 = QPushButton("SpO₂\n-- %")
        self.valor_temperatura = QPushButton("Temperatura\n-- °C")
        self.valor_pam = QPushButton("PAM\n-- mmHg")
        for botao in (self.valor_spo2,self.valor_temperatura,self.valor_pam,):
            botao.setCheckable(True)

            botao.setObjectName("card_sinal")

            botao.setMinimumHeight(65)

            botao.setToolTip(
                "Clique para visualizar "
                "este sinal individualmente."
            )

        #conexaõ dos botão com o ato de clicar
        self.valor_spo2.clicked.connect(lambda: self.selecionar_grafico_sinal("spo2"))

        self.valor_temperatura.clicked.connect(lambda: self.selecionar_grafico_sinal("temperatura"))

        self.valor_pam.clicked.connect(lambda: self.selecionar_grafico_sinal("pam"))

        for botao in (self.valor_spo2, self.valor_temperatura, self.valor_pam):
            botao.setStyleSheet(
                """
                QPushButton {
                    background-color: #f5f7f9;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: center;
                }
                """
            )

        linha_valores.addWidget(self.valor_spo2)
        linha_valores.addWidget(self.valor_temperatura)
        linha_valores.addWidget(self.valor_pam)
        layout.addLayout(linha_valores)

        self.grafico = QChart()
        self.grafico.setTitle("Sinais Vitais — Visão Geral")
        self.grafico.setTheme(QChart.ChartTheme.ChartThemeLight)
        self.grafico.setBackgroundVisible(True)
        self.grafico.setBackgroundBrush(QBrush(QColor("#ffffff")))
        self.grafico.setPlotAreaBackgroundVisible(True)
        self.grafico.setPlotAreaBackgroundBrush(QBrush(QColor("#ffffff")))
        self.grafico.setTitleBrush(QBrush(QColor("#333333")))
        self.grafico.legend().setVisible(True)
        self.grafico.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.grafico.legend().setLabelColor(QColor("#333333"))
        self.grafico.setAnimationOptions(QChart.AnimationOption.NoAnimation) # Animação desativada para plotagem contínua fluida

        self.grafico_view = QChartView(self.grafico)
        self.grafico_view.setFrameShape(QFrame.Shape.NoFrame)
        self.grafico_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.grafico_view.setStyleSheet("background-color: #ffffff;")
        layout.addWidget(self.grafico_view, 1)

        # Mapeamento e estilo das 8 séries de dados (Cor distinta para cada parâmetro)
        self.series_map = {
           "spo2": (QLineSeries(),"SpO₂ (%)",QColor("#27ae60"),),
            "temperatura": (QLineSeries(),"Temperatura (°C)",QColor("#9b59b6"),),
            "pam": (QLineSeries(),"PAM (mmHg)",QColor("#e67e22"),),
        }

        for key, (series, label, color) in self.series_map.items():
            series.setName(label)
            pen = QPen(color)
            pen.setWidthF(3.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            series.setPen(pen)
            series.setBrush(QBrush(color))
            series.setPointsVisible(True)
            series.setMarkerSize(4.0)
            self.grafico.addSeries(series)

        # Configuração dos Eixos
        self.axis_x = QCategoryAxis()
        self.axis_x.setTitleText("Horário Decorrido")

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 180) # Amplitude abrangendo os principais sinais vitais
        self.axis_y.setTitleText("Valor")

        cor_texto_eixos = QColor("#333333")
        cor_grade = QColor("#d9d9d9")
        caneta_grade = QPen(cor_grade)
        self.axis_x.setLabelsBrush(QBrush(cor_texto_eixos))
        self.axis_x.setTitleBrush(QBrush(cor_texto_eixos))
        self.axis_x.setGridLinePen(caneta_grade)
        self.axis_y.setLabelsBrush(QBrush(cor_texto_eixos))
        self.axis_y.setTitleBrush(QBrush(cor_texto_eixos))
        self.axis_y.setGridLinePen(caneta_grade)

        self.grafico.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.grafico.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        for series, _, _ in self.series_map.values():
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        return card

    def update_chart(self, medicao) -> None:
        if not medicao:
            return
        index = self.indice_grafico
        self.indice_grafico += 1
        horario = medicao[0].data_hora.strftime("%H:%M:%S")

        # Dicionário dinâmico com fallback seguro (pega do atributo da medição ou usa 0.0)
        mapa_series = {
        "spo2": "spo2",
        "temperatura": "temperatura",
        "pressao_arterial_media": "pam",
        }

        for medicoes in medicao:
            chave = mapa_series.get(medicoes.parametro.value)

            if chave is None:
                continue

            self.series_map[chave][0].append(
                index,
                float(medicoes.valor),
            )

        JANELA_VISIVEL = 30

        inicio_visivel = max(
            0,
            index - JANELA_VISIVEL + 1,
        )

        self.axis_x.setRange(
            inicio_visivel,
            max(1, index + 1),
        )

        # Exibe um horário a cada 5 leituras,
        # para não poluir o eixo X.
        if index % 5 == 0:
            self.axis_x.append(
                horario,
                index,
            )

        BUFFER_MAXIMO = 120

        for (serie,_,_,) in self.series_map.values():

            excesso = (serie.count() - BUFFER_MAXIMO)

            if excesso > 0:
                serie.removePoints(0,excesso,)

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
        self.paciente["estado_clinico"] = (
            animal["estado_clinico"].capitalize()
        )

        self.paciente["ultima_medicacao"] = (
            animal.get("ultima_medicacao")
            or "Nenhuma"
        )

        self.paciente["quantidade_medicacao"] = (
            animal.get("quantidade")
            or "N/A"
        )

        self.paciente["medico_procedimento"] = (
            animal.get(
                "nome_responsavel",
                "Desconhecido",
            )
        )

        self.atualizar_informacoes_paciente()

        # Para o simulador do paciente anterior.
        # Para o monitoramento anterior.
        if self.simulator is not None:
            self.simulator.stop()

        # Encerra a sessão anterior no banco.
        if self.id_sessao_atual is not None:

            self.repositorio_sessoes.encerrar_sessao(
                self.id_sessao_atual
            )

            self.id_sessao_atual = None


        # Limpa a interface da sessão anterior.
        self.limpar_grafico_monitoramento()


        # Dados da nova sessão.
        id_paciente = int(
            animal["id"]
        )

        usuario_id = int(
            self.usuario["id"]
        )


        # O banco gera o UUID da nova sessão.
        id_sessao = (
            self.repositorio_sessoes
            .iniciar_sessao(
                animal_id=id_paciente,
                usuario_id=usuario_id,
            )
        )

        self.id_sessao_atual = (
            id_sessao
        )


        # Mesmo ID para controlador.
        self.controlador_monitoramento.iniciar_sessao(
            id_paciente=str(
                id_paciente
            ),
            id_sessao=id_sessao,
        )


        # E mesmo ID para simulador.
        self.simulator = SinalVitalSimulacao(
            id_paciente=str(
                id_paciente
            ),
            id_sessao=id_sessao,
            parent=self,
        )

        self.alerta_ia_label.setText(
            "<b>Monitoramento iniciado.</b><br>"
            "Analisando os sinais vitais "
            "do paciente em tempo real."
        )

        self.simulator.measurement_generated.connect(
            self.controlador_monitoramento
            .processar_medicoes
        )

        # Agora inicia e NÃO para depois.
        self.simulator.start()

        pode_editar = (
            e_proprietario
            or
            self.usuario.get("role")
            == "Docente"
        )

        self.btn_editar_paciente.setEnabled(
            pode_editar
        )

        if not pode_editar:
            QMessageBox.information(
                self,
                "Modo Somente Leitura",
                (
                    "Você está monitorando o paciente de "
                    f"{animal.get('nome_responsavel', 'outro usuário')}. "
                    "Alterações nos dados estão desabilitadas."
                ),
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
        self.card_alerta_ia = self.criar_card()
        layout = QVBoxLayout(self.card_alerta_ia)
        self.card_alerta_ia.setObjectName("card_alerta_ia")
        layout.setContentsMargins(18,14,18,14,)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.alerta_ia_label = QLabel(
            (
                "<b>Selecione um animal para "
                "iniciar o monitoramento.</b>"
            )
        )

        self.alerta_ia_label.setTextFormat(Qt.TextFormat.RichText)
        self.alerta_ia_label.setWordWrap(True)
        self.alerta_ia_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #222222;
            }
            """
        )
        self.alerta_ia_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.MinimumExpanding,)
        self.alerta_ia_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        layout.addWidget(self.alerta_ia_label)

        return self.card_alerta_ia

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
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Selecione um animal para "
                    "lançar procedimentos."
                ),
            )
            return

        if self.id_sessao_atual is None:
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Não existe uma sessão de "
                    "monitoramento ativa."
                ),
            )
            return

        dialogo = CadastrarProcedimentoDialog(self.paciente,self,)

        if (
            dialogo.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        dados = dialogo.dados()

        try:
            data_hora = (self._converter_data_hora_registro(dados.get("data"),dados.get("hora"),))

            self.repositorio_procedimentos.salvar(
                sessao_id=(self.id_sessao_atual),
                nome=(dados["procedimento"]),
                executado_por=(dados.get("medico_procedimento")),
                registrado_por=int(self.usuario["id"]),
                data_hora=data_hora,
                observacao=(dados.get("observacao")),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível salvar "
                    "o procedimento.\n\n"
                    f"{erro}"
                ),
            )
            return

        # Só atualiza a interface depois
        # que o banco confirmar o registro.
        self.historico.insert(0,dados,)

        self.paciente["procedimento"] = (dados["procedimento"])

        self.paciente["medico_procedimento"] = dados[ "medico_procedimento"]

        self.atualizar_informacoes_paciente()
        self.atualizar_card_historico()

    def cadastrar_medicacao(self) -> None:
        if self.paciente["nome"] == "---":
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Selecione um animal para "
                    "lançar medicações."
                ),
            )
            return

        if self.id_sessao_atual is None:
            QMessageBox.warning(
                self,
                "Aviso",
                (
                    "Não existe uma sessão de "
                    "monitoramento ativa."
                ),
            )
            return

        dialogo = CadastrarMedicacaoDialog(self.paciente,self,)

        if (
            dialogo.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        dados = dialogo.dados()

        try:
            data_hora = (
                self._converter_data_hora_registro(
                    dados.get("data"),
                    dados.get("hora"),
                )
            )

            self.repositorio_medicacoes.salvar(
                sessao_id=(
                    self.id_sessao_atual
                ),
                nome=(
                    dados["medicacao"]
                ),
                quantidade=float(str(dados["quantidade"]).replace(",", ".")
                ),
                unidade=(
                    dados["unidade"]
                ),
                administrado_por=(
                    dados.get(
                        "medico_medicacao"
                    )
                ),
                registrado_por=int(
                    self.usuario["id"]
                ),
                data_hora=data_hora,
                observacao=(
                    dados.get("observacao")
                ),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível salvar "
                    "a medicação.\n\n"
                    f"{erro}"
                ),
            )
            return

        self.historico.insert(
            0,
            dados,
        )

        self.paciente[
            "ultima_medicacao"
        ] = dados[
            "medicacao"
        ]

        self.paciente[
            "quantidade_medicacao"
        ] = (
            f"{dados['quantidade']} "
            f"{dados['unidade']}"
        )

        self.atualizar_informacoes_paciente()
        self.atualizar_card_historico()

    def ver_historico_completo(self) -> None:
        dialogo = HistoricoDialog(self.historico, self)
        dialogo.exec()

    def atualizar_card_historico(self) -> None:
        if not self.historico:
            self.historico_label.setText(
                "Nenhum procedimento ou medicação cadastrada."
            )
            return

        textos = []
        for registro in self.historico[:2]:
            if registro.get("tipo") == "Procedimento":
                textos.append(
                    f"Procedimento: {registro['procedimento']}<br>"
                    f"Médico responsável: {registro['medico_procedimento']}<br>"
                    f"Data: {registro.get('data', '')} "
                    f"Hora: {registro.get('hora', '')}<br><br>"
                )
            else:
                textos.append(
                    f"Responsável: {registro.get('medico_medicacao', '')}<br>"
                    f"Medicação: {registro.get('medicacao', '')} "
                    f"Qtd: {registro.get('quantidade', '')} "
                    f"{registro.get('unidade', '')}<br>"
                    f"Data: {registro.get('data', '')} "
                    f"Hora: {registro.get('hora', '')}<br><br>"
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

            QPushButton#card_sinal {
                background-color: #f7f9fb;
                color: #242424;

                border: 2px solid #e4e8ec;
                border-radius: 12px;

                padding: 8px;

                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#card_sinal:hover {
                background-color: #f0fbfd;

                border: 2px solid #08b9df;
            }

            QPushButton#card_sinal:checked {
                background-color: #eef0ff;

                border: 2px solid #2100b8;

                color: #2100b8;
            }
            """
        )

    def atualizar_spo2(self,valor: float,) -> None:
        self.valor_spo2.setText(f"SpO₂\n{valor:.1f} %")

    def atualizar_temperatura(self,valor: float,) -> None:
        self.valor_temperatura.setText(f"Temperatura\n{valor:.1f} °C")

    def atualizar_pam(self,valor: float,) -> None:
        self.valor_pam.setText(f"PAM\n{valor:.0f} mmHg")

    def atualizar_resumo_monitoramento(self,resumo: dict,) -> None:

        status = resumo[
            "status_geral"
        ]

        analises = resumo[
            "analises"
        ]

        self.analises_atuais = analises

        # -----------------------------
        # AQUECIMENTO
        # -----------------------------

        if status == "aquecimento":

            quantidade_prontas = sum(
                analise["status"]
                != "aquecimento"
                for analise in (
                    analises.values()
                )
            )

            self._aplicar_estilo_alerta(
                "indisponivel"
            )

            self.alerta_ia_label.setText(
                (
                    "<span style='font-size:16px;'>"
                    "<b>◷ Inicializando monitoramento</b>"
                    "</span>"
                    "<br><br>"
                    "O sistema está coletando dados "
                    "suficientes para estabelecer o "
                    "padrão recente do paciente."
                    "<br><br>"
                    f"Parâmetros preparados: "
                    f"<b>{quantidade_prontas}/3</b>"
                )
            )

            return

        # -----------------------------
        # ALERTA
        # -----------------------------

        if status == "alerta":

            analises_alerta = [
                analise
                for analise in (
                    analises.values()
                )
                if analise["status"]
                == "alerta"
            ]

            self._aplicar_estilo_alerta(
                "alerta"
            )

            partes = [
                (
                    "<span style='font-size:24px;"
                    "color:#d32f2f;'>"
                    "<b>⚠ ALERTA ATIVO</b>"
                    "</span>"
                ),
                (
                    "<br>"
                    "O sistema identificou uma "
                    "<b>alteração persistente</b> "
                    "em relação ao comportamento "
                    "recente do paciente."
                ),
            ]

            for analise in (
                analises_alerta
            ):
                partes.append(
                    "<br><br>"
                )

                partes.append(
                    self._montar_bloco_parametro(
                        analise
                    )
                )

            partes.append(
                (
                    "<br><br>"
                    "<span style='color:#555555;'>"
                    "Recomenda-se atenção ao sinal "
                    "indicado e correlação com o "
                    "contexto clínico do paciente."
                    "</span>"
                )
            )

            self.alerta_ia_label.setText(
                "".join(
                    partes
                )
            )

            return

        # -----------------------------
        # OBSERVAÇÃO
        # -----------------------------

        if status == "observacao":

            observacoes = [
                analise
                for analise in (
                    analises.values()
                )
                if analise["status"]
                == "observacao"
            ]

            self._aplicar_estilo_alerta(
                "observacao"
            )

            partes = [
                (
                    "<span style='font-size:17px;"
                    "color:#9a7d0a;'>"
                    "<b>◷ ALTERAÇÃO EM OBSERVAÇÃO</b>"
                    "</span>"
                ),
                (
                    "<br><br>"
                    "Foi identificada uma mudança "
                    "em relação ao padrão recente, "
                    "mas o sistema ainda está "
                    "verificando se ela persiste."
                ),
            ]

            for analise in observacoes:

                partes.append(
                    "<br><br>"
                )

                partes.append(
                    self._montar_bloco_parametro(
                        analise
                    )
                )

            partes.append(
                (
                    "<br><br>"
                    "<span style='color:#666666;'>"
                    "Status: em acompanhamento."
                    "</span>"
                )
            )

            self.alerta_ia_label.setText(
                "".join(
                    partes
                )
            )

            return

        # -----------------------------
        # RECUPERAÇÃO
        # -----------------------------

        if status == "recuperacao":

            recuperacoes = [
                analise
                for analise in (
                    analises.values()
                )
                if analise["status"]
                == "recuperacao"
            ]

            self._aplicar_estilo_alerta(
                "recuperacao"
            )

            partes = [
                (
                    "<span style='font-size:17px;"
                    "color:#2471a3;'>"
                    "<b>↗ SINAL EM RECUPERAÇÃO</b>"
                    "</span>"
                ),
                (
                    "<br><br>"
                    "O parâmetro está retornando "
                    "em direção ao comportamento "
                    "recente do paciente."
                ),
            ]

            for analise in recuperacoes:

                partes.append(
                    "<br><br>"
                )

                partes.append(
                    self._montar_bloco_parametro(
                        analise,
                        mostrar_detalhe_tecnico=False,
                    )
                )

            partes.append(
                (
                    "<br><br>"
                    "<span style='color:#666666;'>"
                    "O sistema continuará acompanhando "
                    "as próximas medições."
                    "</span>"
                )
            )

            self.alerta_ia_label.setText(
                "".join(
                    partes
                )
            )

            return

        # -----------------------------
        # INDISPONÍVEL
        # -----------------------------

        if status == "indisponivel":

            self._aplicar_estilo_alerta(
                "indisponivel"
            )

            self.alerta_ia_label.setText(
                (
                    "<span style='font-size:17px;'>"
                    "<b>⚠ Análise temporariamente "
                    "indisponível</b>"
                    "</span>"
                    "<br><br>"
                    "O sistema não possui dados "
                    "suficientes ou confiáveis para "
                    "avaliar o sinal neste momento."
                    "<br><br>"
                    "<span style='color:#666666;'>"
                    "O monitoramento continuará "
                    "automaticamente."
                    "</span>"
                )
            )

            return

        # -----------------------------
        # NORMAL
        # -----------------------------

        self._aplicar_estilo_alerta(
            "normal"
        )

        partes = [
            (
                "<span style='font-size:17px;"
                "color:#1e8449;'>"
                "<b>✓ MONITORAMENTO ESTÁVEL</b>"
                "</span>"
            ),
            (
                "<br><br>"
                "Nenhuma alteração persistente foi "
                "identificada pelos critérios de "
                "monitoramento do sistema."
            ),
            (
                "<br><br>"
                "<b>Sinais atuais</b>"
            ),
        ]

        ordem = [
            ParametroVital.SPO2,
            ParametroVital.TEMPERATURA,
            ParametroVital.PRESSAO_ARTERIAL_MEDIA,
        ]

        for parametro in ordem:

            analise = analises.get(
                parametro
            )

            if analise is None:
                continue

            if (
                analise["status"]
                != "normal"
            ):
                continue

            partes.append(
                (
                    "<br>"
                    f"{analise['nome']}: "
                    f"<b>{analise['valor']:.2f} "
                    f"{analise['unidade']}</b>"
                )
            )

        partes.append(
            (
                "<br><br>"
                "<span style='color:#666666;'>"
                "Status: acompanhamento contínuo."
                "</span>"
            )
        )

        self.alerta_ia_label.setText(
            "".join(
                partes
            )
        )

    @staticmethod
    def _formatar_z(z_robusto,) -> str:

        if z_robusto is None:
            return "N/A"

        return f"{z_robusto:.2f}"

    def simular_queda_spo2(self,) -> None:

        if self.simulator is None:
            return

        self.simulator.simular_queda_spo2(
            quantidade=3.0
        )


    def simular_queda_pam(
        self,
    ) -> None:

        if self.simulator is None:
            return

        self.simulator.simular_queda_pam(
            quantidade=15.0
        )


    def simular_aumento_temperatura(
        self,
    ) -> None:

        if self.simulator is None:
            return

        self.simulator.simular_aumento_temperatura(
            quantidade=0.8
        )


    def restaurar_sinais_teste(
        self,
    ) -> None:

        if self.simulator is None:
            return

        self.simulator.restaurar_sinais_teste()


    def limpar_grafico_monitoramento(self,) -> None:

        self.indice_grafico = 0

        for (
            serie,
            _,
            _,
        ) in self.series_map.values():

            serie.clear()

        for rotulo in list(
            self.axis_x.categoriesLabels()
        ):
            self.axis_x.remove(
                rotulo
            )

        self.axis_x.setRange(
            0,
            1,
        )
    @staticmethod
    def _converter_data_hora_registro(data,hora,) -> datetime:

        if isinstance(data, datetime):
            return data

        texto_data = str(data).strip()
        texto_hora = str(hora).strip()

        texto_completo = (
            f"{texto_data} {texto_hora}"
        ).strip()

        formatos = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

        for formato in formatos:
            try:
                return datetime.strptime(
                    texto_completo,
                    formato,
                )

            except ValueError:
                continue

        raise ValueError(
            "Formato de data/hora não reconhecido: "
            f"{texto_completo}"
        )

    def gerar_relatorio(self,) -> None:

        if self.id_sessao_atual is None:

            QMessageBox.warning(
                self,
                "Relatório",
                (
                    "Selecione um animal e inicie "
                    "o monitoramento antes de gerar "
                    "o relatório."
                ),
            )

            return

        if (
            self.thread_relatorio is not None
            and self.thread_relatorio.isRunning()
        ):
            return

        # Fecha o menu lateral.
        self.fechar_menu()

        self.btn_relatorio.setEnabled(
            False
        )

        self.btn_relatorio.setText(
            "Gerando relatório..."
        )

        self.thread_relatorio = QThread(
            self
        )

        self.worker_relatorio = (
            WorkerRelatorio(
                id_sessao=(
                    self.id_sessao_atual
                ),
                analises_atuais=(
                    self.analises_atuais
                ),
            )
        )

        self.worker_relatorio.moveToThread(
            self.thread_relatorio
        )

        self.thread_relatorio.started.connect(
            self.worker_relatorio.executar
        )

        self.worker_relatorio.relatorio_gerado.connect(
            self._relatorio_gerado
        )

        self.worker_relatorio.erro.connect(
            self._erro_geracao_relatorio
        )

        self.worker_relatorio.finalizado.connect(
            self.thread_relatorio.quit
        )

        self.worker_relatorio.finalizado.connect(
            self.worker_relatorio.deleteLater
        )

        self.thread_relatorio.finished.connect(
            self._finalizar_geracao_relatorio
        )

        self.thread_relatorio.start()

    def _relatorio_gerado(self,relatorio,) -> None:

        self.relatorio_ia_atual = (
            relatorio
        )

        print()
        print(
            "[M.I.S.A] Relatório por IA gerado."
        )

        print(
            relatorio.resumo_geral
        )

        QMessageBox.information(
            self,
            "Relatório",
            (
                "O conteúdo do relatório foi "
                "gerado com sucesso.\n\n"
                "A exportação para PDF será "
                "integrada a seguir."
            ),
        )

    def _erro_geracao_relatorio(
        self,
        mensagem: str,
    ) -> None:

        QMessageBox.critical(
            self,
            "Erro ao gerar relatório",
            (
                "Não foi possível gerar "
                "o relatório por IA.\n\n"
                f"{mensagem}"
            ),
        )

    def _finalizar_geracao_relatorio(
        self,
    ) -> None:

        self.btn_relatorio.setEnabled(
            True
        )

        self.btn_relatorio.setText(
            "Relatório..."
        )

        if self.thread_relatorio is not None:
            self.thread_relatorio.deleteLater()

        self.thread_relatorio = None
        self.worker_relatorio = None

    def selecionar_grafico_sinal(self,parametro: str,) -> None:
        # Se clicar novamente no parâmetro
        # que já está selecionado,
        # volta para visão geral.
        if (self.parametro_grafico_selecionado == parametro):
            self.parametro_grafico_selecionado = (None)

        else:
            self.parametro_grafico_selecionado = (parametro)

        self._atualizar_modo_grafico()

    def _atualizar_modo_grafico(self,) -> None:

        parametro = (
            self.parametro_grafico_selecionado
        )

        botoes = {
            "spo2": self.valor_spo2,
            "temperatura": (
                self.valor_temperatura
            ),
            "pam": self.valor_pam,
        }

        for (
            chave,
            botao,
        ) in botoes.items():

            botao.setChecked(
                chave == parametro
            )

        for (
            chave,
            (
                serie,
                _,
                _,
            ),
        ) in self.series_map.items():

            serie.setVisible(
                parametro is None
                or chave == parametro
            )

        self._configurar_escala_grafico(
            parametro
        )

    def _configurar_escala_grafico(
        self,
        parametro: str | None,
    ) -> None:

        if parametro is None:

            self.grafico.setTitle(
                "Sinais Vitais — Visão Geral"
            )

            self.axis_y.setTitleText(
                "Valor"
            )

            self.axis_y.setRange(
                0,
                160
            )

            self.axis_y.setLabelFormat(
                "%.0f"
            )

            self.grafico.legend().setVisible(
                True
            )

            return

        configuracoes = {
            "spo2": {
                "titulo": "SpO₂ — Detalhamento",
                "eixo": "Saturação (%)",
                "minimo": 70,
                "maximo": 100,
                "formato": "%.0f",
            },

            "temperatura": {
                "titulo": (
                    "Temperatura — Detalhamento"
                ),
                "eixo": "Temperatura (°C)",
                "minimo": 34,
                "maximo": 42,
                "formato": "%.1f",
            },

            "pam": {
                "titulo": "PAM — Detalhamento",
                "eixo": "PAM (mmHg)",
                "minimo": 20,
                "maximo": 160,
                "formato": "%.0f",
            },
        }

        configuracao = (
            configuracoes[parametro]
        )

        self.grafico.setTitle(
            configuracao["titulo"]
        )

        self.axis_y.setTitleText(
            configuracao["eixo"]
        )

        self.axis_y.setRange(
            configuracao["minimo"],
            configuracao["maximo"],
        )

        self.axis_y.setLabelFormat(
            configuracao["formato"]
        )

        self.grafico.legend().setVisible(
            False
        )
    def _obter_referencia_recente(self,analise: dict,) -> float | None:

        valor = analise.get("mediana")

        if valor is None:
            return None

        return float(valor)

    def _formatar_variacao_sinal(self,analise: dict,) -> str:

        valor_atual = analise.get("valor")

        referencia = (self._obter_referencia_recente(analise))

        unidade = analise.get("unidade", "",)

        if (valor_atual is None or referencia is None):
            return (
                "Comparação com o padrão recente "
                "indisponível."
            )

        diferenca = (float(valor_atual) - float(referencia))

        if abs(diferenca) < 0.01:
            return (
                "Valor atual muito próximo "
                "da referência recente."
            )

        if diferenca < 0:
            direcao = "redução"
        else:
            direcao = "aumento"

        return (
            f"{direcao.capitalize()} de "
            f"{abs(diferenca):.2f} {unidade} "
            f"em relação à referência recente."
        )

    def _montar_bloco_parametro(self,analise: dict,mostrar_detalhe_tecnico: bool = True,) -> str:

        nome = analise.get("nome","Parâmetro",)

        valor = analise.get("valor")

        unidade = analise.get("unidade","",)

        referencia = (self._obter_referencia_recente(analise))

        z_robusto = analise.get("z_robusto")

        if valor is None:
            texto_valor = "Indisponível"
        else:
            texto_valor = (
                f"{float(valor):.2f} "
                f"{unidade}"
            )

        partes = [
            (
                f"<b>{nome}</b><br>"
                f"Valor atual: "
                f"<b>{texto_valor}</b>"
            )
        ]

        if referencia is not None:
            partes.append(
                (
                    "<br>"
                    "Referência recente: "
                    f"{referencia:.2f} "
                    f"{unidade}"
                )
            )

            partes.append(
                (
                    "<br>"
                    f"{self._formatar_variacao_sinal(analise)}"
                )
            )

        if (mostrar_detalhe_tecnico and z_robusto is not None):
            partes.append(
                (
                    "<br>"
                    "<span style='color:#777777;"
                    "font-size:11px;'>"
                    "Detalhe técnico do sistema: "
                    f"índice estatístico = "
                    f"{z_robusto:.2f}"
                    "</span>"
                )
            )

        return "".join(partes)

    def _estilo_alerta_base(self, estado: str) -> str:
        estilos = {
            "normal": """
                QFrame#card_alerta_ia {
                    background-color: white;
                    border: 2px solid #d9eee4;
                    border-radius: 12px;
                }
            """,
            "observacao": """
                QFrame#card_alerta_ia {
                    background-color: #fffdf5;
                    border: 2px solid #f1c40f;
                    border-radius: 12px;
                }
            """,
            "alerta": """
                QFrame#card_alerta_ia {
                    background-color: #fff8f8;
                    border: 3px solid #ff8a8a;
                    border-radius: 16px;
                }
            """,
            "recuperacao": """
                QFrame#card_alerta_ia {
                    background-color: #f6fbff;
                    border: 2px solid #3498db;
                    border-radius: 12px;
                }
            """,
            "indisponivel": """
                QFrame#card_alerta_ia {
                    background-color: #fafafa;
                    border: 2px solid #b0b0b0;
                    border-radius: 12px;
                }
            """,
        }
        return estilos.get(estado, estilos["normal"])

    def _aplicar_estilo_alerta(self, estado: str) -> None:
        self.estado_alerta_atual = estado

        if estado == "alerta":
            self.iniciar_animacao_alerta()
        else:
            self.parar_animacao_alerta()

    def iniciar_animacao_alerta(self) -> None:
        if self.alerta_animacao_timer.isActive():
            return

        self.alerta_animacao_fase_forte = False
        self.card_alerta_ia.setStyleSheet(
            self._estilo_alerta_base("alerta")
        )
        self.sombra_alerta.setBlurRadius(20)
        self.sombra_alerta.setColor(QColor(255, 80, 80, 90))
        self.alerta_animacao_timer.start(380)

    def parar_animacao_alerta(self) -> None:
        if self.alerta_animacao_timer.isActive():
            self.alerta_animacao_timer.stop()

        self.alerta_animacao_fase_forte = False
        self.card_alerta_ia.setStyleSheet(
            self._estilo_alerta_base(self.estado_alerta_atual)
        )
        self.sombra_alerta.setBlurRadius(20)
        self.sombra_alerta.setColor(QColor(255, 0, 0, 0))

    def _alternar_animacao_alerta(self) -> None:
        self.alerta_animacao_fase_forte = (
            not self.alerta_animacao_fase_forte
        )

        if self.alerta_animacao_fase_forte:
            self.card_alerta_ia.setStyleSheet(
                """
                QFrame#card_alerta_ia {
                    background-color: #fff1f1;
                    border: 5px solid #ff2b2b;
                    border-radius: 16px;
                }
                """
            )
            self.sombra_alerta.setBlurRadius(35)
            self.sombra_alerta.setColor(QColor(255, 0, 0, 180))
        else:
            self.card_alerta_ia.setStyleSheet(
                """
                QFrame#card_alerta_ia {
                    background-color: #fff8f8;
                    border: 3px solid #ff8a8a;
                    border-radius: 16px;
                }
                """
            )
            self.sombra_alerta.setBlurRadius(20)
            self.sombra_alerta.setColor(QColor(255, 80, 80, 90))
