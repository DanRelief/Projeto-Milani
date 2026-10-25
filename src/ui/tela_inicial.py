from datetime import datetime
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
    QThread,
    QTimer,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QPixmap,
    QTextDocument,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import (
    QCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)

from infrastructure.repositories.repositorio_sessoes import RepositorioSessoes

from ..application.monitoramento.controlador_monitoramento import ControladorMonitoramento
from ..domain.measurement import ParametroVital
from ..infrastructure.simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .cadastrar_animal import DialogCadastrarAnimal
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .selecionar_animal import DialogSelecionarAnimal

from src.ia.llm.worker_relatorio import WorkerRelatorio
from src.infrastructure.database import (
    carregar_historico_animal,
    deletar_historico_medicacao,
    deletar_historico_procedimento,
    salvar_historico_medicacao,
    salvar_historico_procedimento,
    salvar_observacao_docente,
)

class TelaInicial(QMainWindow):
    logout_requested = Signal()

    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.usuario = usuario

        papel_usuario = str(
            usuario.get("role")
            or usuario.get("papel")
            or ""
        ).strip().lower()
        self.is_teacher = papel_usuario in {
            "teacher",
            "docente",
            "professor",
            "admin",
        }

        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(1024, 720)
        self.setMinimumSize(900, 650)

        self.indice_grafico = 0
        self.parametro_grafico_selecionado = None
        self.id_sessao_atual = None

        self.repositorio_sessoes = RepositorioSessoes()

        self.thread_relatorio = None
        self.worker_relatorio = None
        self.relatorio_ia_atual = None
        self.analises_atuais = {}
        self.dialogo_progresso_relatorio = None
        self.caminho_relatorio_ia_pendente = None

        self.estado_alerta_atual = "normal"
        self.alerta_animacao_timer = QTimer(self)
        self.alerta_animacao_timer.timeout.connect(
            self._alternar_animacao_alerta
        )
        self.alerta_animacao_fase_forte = False
        self.sombra_alerta = None

        self.paciente = {
            "id": None,
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
            "observacao_docente": "",
            "responsavel_id": None,
        }

        self.historico = []

        # Simulador + pipeline de análise/IA do monitoramento.
        self.simulator = None
        self.controlador_monitoramento = ControladorMonitoramento(parent=self)
        self.controlador_monitoramento.medicoes_atualizadas.connect(
            self.update_chart
        )
        self.controlador_monitoramento.spo2_atualizada.connect(
            self.atualizar_spo2
        )
        self.controlador_monitoramento.temperatura_atualizada.connect(
            self.atualizar_temperatura
        )
        self.controlador_monitoramento.pam_atualizada.connect(
            self.atualizar_pam
        )
        self.controlador_monitoramento.resumo_monitoramento_atualizado.connect(
            self.atualizar_resumo_monitoramento
        )

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
        layout_cabecalho.setSpacing(16)

        diretorio_atual = Path(__file__).resolve().parent
        pasta_assets = None
        for pai in [diretorio_atual] + list(diretorio_atual.parents):
            candidato = pai / "assets"
            if candidato.is_dir():
                pasta_assets = candidato
                break

        if pasta_assets is None:
            pasta_assets = Path(__file__).resolve().parents[2] / "assets"

        caminho_logo = None
        if self.is_teacher:
            for nome_arquivo in (
                "logo_misa_docente.jpg",
                "logo_misa_docente.png",
                "logo_misa_verde.png",
            ):
                candidato = pasta_assets / nome_arquivo
                if candidato.exists():
                    caminho_logo = candidato
                    break

        if caminho_logo is None or not caminho_logo.exists():
            caminho_logo = pasta_assets / "logo_misa.png"

        logo = QLabel()
        imagem_logo = QPixmap(str(caminho_logo))
        if not imagem_logo.isNull():
            logo.setPixmap(
                imagem_logo.scaled(
                    200,
                    70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

        nome_usuario = usuario.get("name") or usuario.get("nome") or ""
        identificador = (
            usuario.get("identifier")
            or usuario.get("identificador")
            or ""
        )
        rotulo_identificador = usuario.get("identifier_label") or (
            "E-mail" if self.is_teacher else "RA"
        )
        rotulo_papel = usuario.get("role") or usuario.get("papel") or (
            "Docente" if self.is_teacher else "Aluno"
        )

        dados_usuario = QLabel(
            f'<span style="color:{cor_destaque};"><b>{rotulo_papel}:</b></span> '
            f'{nome_usuario}<br>'
            f'<span style="color:{cor_destaque};"><b>{rotulo_identificador}:</b></span> '
            f'{identificador}'
        )

        nome_professor = usuario.get("professor_name", "Milani")
        dados_professor = QLabel(
            f'<span style="color:{cor_destaque};"><b>Professor:</b></span> '
            f'{nome_professor}'
        )

        botao_menu = QPushButton("\u2630")
        botao_menu.setObjectName("botao_menu")
        botao_menu.clicked.connect(self.alternar_menu)

        titulo = QLabel("M.I.S.A")
        titulo.setStyleSheet(
            f"font-size: 38px; font-weight: bold; color: {cor_destaque};"
        )

        layout_cabecalho.addWidget(logo)
        layout_cabecalho.addWidget(
            titulo,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout_cabecalho.addWidget(
            dados_usuario,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout_cabecalho.addStretch()
        layout_cabecalho.addWidget(
            dados_professor,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout_cabecalho.addWidget(
            botao_menu,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )

        layout_fundo.addWidget(cabecalho)

        conteudo_widget = self.montar_conteudo()
        layout_fundo.addWidget(conteudo_widget, 1)

        # Sombra fixa; a animação varia apenas cor/estilo, evitando tremor.
        self.sombra_alerta = QGraphicsDropShadowEffect(self.card_alerta_ia)
        self.sombra_alerta.setBlurRadius(20)
        self.sombra_alerta.setOffset(0, 0)
        self.sombra_alerta.setColor(QColor(255, 0, 0, 0))
        self.card_alerta_ia.setGraphicsEffect(self.sombra_alerta)

        self._aplicar_estilos()
        self.setCentralWidget(central)
        self.montar_menu_lateral(central, usuario)

    def montar_menu_lateral(
        self,
        central: QWidget,
        usuario: dict[str, str],
    ) -> None:
        """Cria o painel lateral com tema adequado ao perfil logado."""
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
        self.btn_relatorio.setToolTip(
            "Gerar relatório do monitoramento com apoio da IA"
        )
        self.btn_relatorio.clicked.connect(self.gerar_relatorio)
        layout.addWidget(self.btn_relatorio)

        layout.addStretch()

        caminho_logo = Path(__file__).resolve().parents[2] / "assets" / "logo_misa.png"
        logo_menu = QLabel()
        if caminho_logo.exists():
            imagem_logo = QPixmap(str(caminho_logo))
            if not imagem_logo.isNull():
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

        cor_tema = "#287a55" if self.is_teacher else "#08b9df"
        cor_hover = "#216746" if self.is_teacher else "#078eaa"
        cor_fechar = "#1f4d3a" if self.is_teacher else "#2100b8"
        cor_fechar_hover = "#183e2e" if self.is_teacher else "#351bc9"

        self.menu_overlay.setStyleSheet(
            f"""
            QFrame#menu_overlay {{
                background-color: rgba(0, 0, 0, 155);
            }}

            QFrame#menu_panel {{
                background-color: #ffffff;
                border-radius: 16px;
                border-right: 3px solid {cor_tema};
            }}

            QPushButton#botao_fechar_menu {{
                background-color: {cor_fechar};
                color: #ffffff;
                border: none;
                border-radius: 22px;
                padding: 6px 18px;
                min-height: 32px;
                font-size: 25px;
                font-weight: bold;
            }}

            QPushButton#botao_fechar_menu:hover {{
                background-color: {cor_fechar_hover};
            }}

            QPushButton#item_menu {{
                color: {cor_tema};
                background-color: transparent;
                border: none;
                padding: 6px 10px;
                font-size: 20px;
                font-weight: bold;
                text-align: left;
            }}

            QPushButton#item_menu:hover {{
                color: {cor_hover};
            }}
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

        nome = usuario.get("name") or usuario.get("nome") or ""
        identificador = (
            usuario.get("identifier")
            or usuario.get("identificador")
            or ""
        )
        rotulo = usuario.get("identifier_label") or (
            "E-mail" if self.is_teacher else "RA"
        )
        papel = usuario.get("role") or usuario.get("papel") or ""

        QMessageBox.information(
            self,
            "Perfil",
            f"Nome: {nome}\n{rotulo}: {identificador}\nPerfil: {papel}",
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

        # Mantém o gráfico e o alerta com o espaço da versão de IA, mas
        # reserva altura suficiente para observações/permissões do docente.
        card_paciente.setMinimumHeight(390)
        card_historico.setMinimumHeight(220)
        card_monitoramento.setMinimumHeight(380)
        card_alertas.setMinimumHeight(220)

        card_historico.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        card_alertas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        coluna_esquerda = QVBoxLayout()
        coluna_direita = QVBoxLayout()

        coluna_esquerda.addWidget(
            self.criar_secao_card("INFORMAÇÕES DO PACIENTE", card_paciente)
        )
        coluna_esquerda.addWidget(
            self.criar_secao_card("HISTÓRICO", card_historico)
        )

        coluna_direita.addWidget(
            self.criar_secao_card(
                "MONITORAMENTO EM TEMPO REAL",
                card_monitoramento,
            )
        )
        coluna_direita.addWidget(
            self.criar_secao_card("ALERTAS DE IA", card_alertas)
        )

        grade.addLayout(coluna_esquerda, 0, 0)
        grade.addLayout(coluna_direita, 0, 1)
        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(1, 2)
        grade.setRowStretch(0, 1)

        return conteudo

    def exportar_relatorio_pdf(
        self,
        incluir_relatorio_ia: bool | None = None,
    ) -> None:
        """Exporta paciente, gráfico, histórico e, quando disponível, relatório IA."""
        if not self.paciente.get("nome") or self.paciente.get("nome") == "---":
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um animal antes de exportar o relatório.",
            )
            return

        if incluir_relatorio_ia is None:
            incluir_relatorio_ia = False

        nome_seguro = str(self.paciente.get("nome", "paciente")).strip() or "paciente"
        nome_sugerido = f"Relatorio_MISA_{nome_seguro}.pdf"
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório em PDF",
            nome_sugerido,
            "Arquivos PDF (*.pdf)",
        )

        if not caminho_arquivo:
            return

        if not caminho_arquivo.lower().endswith(".pdf"):
            caminho_arquivo += ".pdf"

        cor_tema = "#287a55" if self.is_teacher else "#08b9df"
        cor_cabecalho_tabela = "#216746" if self.is_teacher else "#078eaa"

        caminho_img_temp = Path(__file__).resolve().parent / "temp_grafico_misa.png"

        def texto(valor, padrao="-") -> str:
            if valor is None or str(valor).strip() == "":
                return escape(str(padrao))
            return escape(str(valor))

        try:
            pixmap_grafico = self.grafico_view.grab()
            pixmap_grafico.save(str(caminho_img_temp), "PNG")

            linhas_historico = []
            for registro in self.historico:
                data_hora = (
                    f"{registro.get('data', '')} {registro.get('hora', '')}"
                ).strip()

                if registro.get("tipo") == "Procedimento":
                    detalhe = (
                        f"<b>Procedimento:</b> {texto(registro.get('procedimento'))}"
                    )
                    descricao = registro.get("descricao_detalhada")
                    if descricao:
                        detalhe += f"<br>{texto(descricao)}"
                    responsavel = texto(registro.get("medico_procedimento"))
                else:
                    dose = registro.get("quantidade") or "Não informada"
                    detalhe = (
                        f"<b>Medicação:</b> {texto(registro.get('medicacao'))} "
                        f"({texto(dose)})"
                    )
                    via = registro.get("via_administracao")
                    if via:
                        detalhe += f"<br><b>Via:</b> {texto(via)}"
                    responsavel = texto(registro.get("medico_medicacao"))

                linhas_historico.append(
                    "<tr>"
                    f"<td>{texto(data_hora)}</td>"
                    f"<td><b>{texto(registro.get('tipo', 'Registro'))}</b></td>"
                    f"<td>{detalhe}</td>"
                    f"<td>{responsavel}</td>"
                    "</tr>"
                )

            if not linhas_historico:
                linhas_historico.append(
                    "<tr><td colspan='4' style='text-align:center;'>"
                    "<i>Nenhum procedimento ou medicação cadastrado.</i>"
                    "</td></tr>"
                )

            secao_ia = ""
            relatorio = self.relatorio_ia_atual
            if incluir_relatorio_ia and relatorio is not None:
                def lista_html(itens) -> str:
                    itens = list(itens or [])
                    if not itens:
                        return "<p><i>Nenhum item informado.</i></p>"
                    return "<ul>" + "".join(
                        f"<li>{texto(item)}</li>" for item in itens
                    ) + "</ul>"

                secao_ia = f"""
                    <h2>4. Análise do monitoramento com IA</h2>
                    <div class="info-box">
                        <b>Resumo geral</b><br>
                        {texto(getattr(relatorio, 'resumo_geral', ''))}
                    </div>

                    <h3>Evolução dos sinais</h3>
                    {lista_html(getattr(relatorio, 'evolucao_sinais', []))}

                    <h3>Eventos relevantes</h3>
                    {lista_html(getattr(relatorio, 'eventos_relevantes', []))}

                    <h3>Relações temporais</h3>
                    {lista_html(getattr(relatorio, 'relacoes_temporais', []))}

                    <h3>Informações ausentes</h3>
                    {lista_html(getattr(relatorio, 'informacoes_ausentes', []))}

                    <h3>Observações</h3>
                    {lista_html(getattr(relatorio, 'observacoes', []))}

                    <div class="aviso">
                        {texto(getattr(relatorio, 'aviso', ''))}
                    </div>
                """

            observacao_docente = self.paciente.get("observacao_docente")
            if not observacao_docente:
                observacao_docente = "Nenhuma observação registrada."

            nome_usuario = self.usuario.get("name") or self.usuario.get("nome") or "Usuário"
            papel_usuario = self.usuario.get("role") or self.usuario.get("papel") or "Usuário"

            conteudo_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        color: #1a1a1a;
                        background-color: #ffffff;
                        font-size: 10.5pt;
                    }}
                    h1 {{
                        color: {cor_tema};
                        border-bottom: 2px solid {cor_tema};
                        padding-bottom: 6px;
                        font-size: 20pt;
                    }}
                    h2 {{
                        color: {cor_tema};
                        margin-top: 18px;
                        border-bottom: 1px solid #cccccc;
                        padding-bottom: 4px;
                        font-size: 14pt;
                    }}
                    h3 {{ color: {cor_tema}; font-size: 12pt; }}
                    .info-box {{
                        background-color: #f2f4f7;
                        border: 1px solid #b0bec5;
                        padding: 10px;
                        margin-bottom: 12px;
                        line-height: 1.45;
                    }}
                    .info-box b {{ color: {cor_tema}; }}
                    .aviso {{
                        margin-top: 14px;
                        padding: 10px;
                        border: 1px solid #d0d0d0;
                        background-color: #fffdf5;
                        font-style: italic;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 8px;
                        table-layout: fixed;
                    }}
                    th {{
                        background-color: {cor_cabecalho_tabela};
                        color: #ffffff;
                        padding: 7px;
                        text-align: left;
                    }}
                    td {{
                        padding: 7px;
                        border-bottom: 1px solid #d0d0d0;
                        word-wrap: break-word;
                    }}
                </style>
            </head>
            <body>
                <h1>M.I.S.A. - Relatório de Monitoramento Animal</h1>

                <div class="info-box">
                    <b>Paciente:</b> {texto(self.paciente.get('nome'))} &nbsp;|&nbsp;
                    <b>Espécie:</b> {texto(self.paciente.get('especie'))} &nbsp;|&nbsp;
                    <b>Idade:</b> {texto(self.paciente.get('idade'), 0)} anos &nbsp;|&nbsp;
                    <b>Porte:</b> {texto(self.paciente.get('porte'))}<br><br>
                    <b>Responsável:</b> {texto(self.paciente.get('medico_procedimento'))}<br>
                    <b>Emitido por:</b> {texto(nome_usuario)} ({texto(papel_usuario)})
                </div>

                <h2>1. Gráfico de sinais vitais</h2>
                <div style="text-align:center; margin:10px 0;">
                    <img src="{caminho_img_temp.as_uri()}"
                         style="width:100%; max-width:520px; height:auto;" />
                </div>

                <h2>2. Observações do docente</h2>
                <div class="info-box">{texto(observacao_docente)}</div>

                <h2>3. Histórico de procedimentos e medicações</h2>
                <table>
                    <thead>
                        <tr>
                            <th width="22%">Data / Hora</th>
                            <th width="15%">Tipo</th>
                            <th width="43%">Descrição / Detalhes</th>
                            <th width="20%">Responsável</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(linhas_historico)}
                    </tbody>
                </table>

                {secao_ia}
            </body>
            </html>
            """

            documento = QTextDocument()
            documento.setHtml(conteudo_html)

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho_arquivo)
            documento.print_(printer)

            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório PDF gerado com sucesso!\n\nSalvo em:\n{caminho_arquivo}",
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro na geração",
                f"Não foi possível gerar o PDF: {erro}",
            )

        finally:
            if caminho_img_temp.exists():
                try:
                    caminho_img_temp.unlink()
                except OSError:
                    pass

    def _capturar_graficos_relatorio_ia(
        self,
        pasta_temporaria: Path,
    ) -> dict[str, Path]:
        """Captura a visão geral e os três gráficos individuais do relatório IA.

        O mesmo QChartView da interface é reutilizado para preservar séries,
        escalas e dados. Ao final, o modo de visualização anterior é restaurado.
        """
        parametro_original = self.parametro_grafico_selecionado
        caminhos: dict[str, Path] = {}

        modos = (
            (None, "geral", 65, "Capturando gráfico geral..."),
            ("spo2", "spo2", 72, "Capturando gráfico de SpO₂..."),
            ("temperatura", "temperatura", 79, "Capturando gráfico de Temperatura..."),
            ("pam", "pam", 86, "Capturando gráfico de PAM..."),
        )

        try:
            for parametro, nome_arquivo, progresso, mensagem in modos:
                self._atualizar_progresso_relatorio(progresso, mensagem)
                self.parametro_grafico_selecionado = parametro
                self._atualizar_modo_grafico()

                # Processa a alteração de visibilidade, título e escala antes
                # de capturar a imagem.
                QCoreApplication.processEvents()

                caminho = pasta_temporaria / f"grafico_{nome_arquivo}.png"
                pixmap = self.grafico_view.grab()

                if pixmap.isNull() or not pixmap.save(str(caminho), "PNG"):
                    raise RuntimeError(
                        f"Não foi possível capturar o gráfico: {nome_arquivo}."
                    )

                caminhos[nome_arquivo] = caminho

        finally:
            self.parametro_grafico_selecionado = parametro_original
            self._atualizar_modo_grafico()
            QCoreApplication.processEvents()

        return caminhos

    def exportar_relatorio_completo_ia(
        self,
        caminho_arquivo: str | None = None,
    ) -> bool:
        """Gera o relatório unificado do M.I.S.A. com histórico, IA e 4 gráficos."""
        if not self.paciente.get("nome") or self.paciente.get("nome") == "---":
            QMessageBox.warning(
                self,
                "Relatório com IA",
                "Selecione um animal antes de gerar o relatório.",
            )
            return

        relatorio = self.relatorio_ia_atual
        if relatorio is None:
            QMessageBox.warning(
                self,
                "Relatório com IA",
                "A análise por IA ainda não foi gerada para esta sessão.",
            )
            return

        if caminho_arquivo is None:
            nome_seguro = (
                str(self.paciente.get("nome", "paciente")).strip() or "paciente"
            )
            nome_sugerido = f"Relatorio_MISA_IA_{nome_seguro}.pdf"
            caminho_arquivo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Relatório Completo com IA",
                nome_sugerido,
                "Arquivos PDF (*.pdf)",
            )

        if not caminho_arquivo:
            return False

        if not caminho_arquivo.lower().endswith(".pdf"):
            caminho_arquivo += ".pdf"

        cor_tema = "#287a55" if self.is_teacher else "#08b9df"
        cor_cabecalho_tabela = "#216746" if self.is_teacher else "#078eaa"

        def texto(valor, padrao="-") -> str:
            if valor is None or str(valor).strip() == "":
                return escape(str(padrao))
            return escape(str(valor))

        def lista_html(itens) -> str:
            itens = list(itens or [])
            if not itens:
                return "<p><i>Nenhum item informado.</i></p>"
            return "<ul>" + "".join(
                f"<li>{texto(item)}</li>" for item in itens
            ) + "</ul>"

        try:
            self._atualizar_progresso_relatorio(60, "Preparando dados do relatório...")

            with TemporaryDirectory(prefix="misa_relatorio_ia_") as pasta_temp:
                caminhos_graficos = self._capturar_graficos_relatorio_ia(
                    Path(pasta_temp)
                )

                self._atualizar_progresso_relatorio(90, "Montando conteúdo do PDF...")

                linhas_historico = []
                for registro in self.historico:
                    data_hora = (
                        f"{registro.get('data', '')} {registro.get('hora', '')}"
                    ).strip()

                    if registro.get("tipo") == "Procedimento":
                        detalhe = (
                            f"<b>Procedimento:</b> "
                            f"{texto(registro.get('procedimento'))}"
                        )
                        descricao = registro.get("descricao_detalhada")
                        if descricao:
                            detalhe += f"<br>{texto(descricao)}"
                        responsavel = texto(registro.get("medico_procedimento"))
                    else:
                        dose = registro.get("quantidade") or "Não informada"
                        detalhe = (
                            f"<b>Medicação:</b> {texto(registro.get('medicacao'))} "
                            f"({texto(dose)})"
                        )
                        via = registro.get("via_administracao")
                        if via:
                            detalhe += f"<br><b>Via:</b> {texto(via)}"
                        responsavel = texto(registro.get("medico_medicacao"))

                    linhas_historico.append(
                        "<tr>"
                        f"<td>{texto(data_hora)}</td>"
                        f"<td><b>{texto(registro.get('tipo', 'Registro'))}</b></td>"
                        f"<td>{detalhe}</td>"
                        f"<td>{responsavel}</td>"
                        "</tr>"
                    )

                if not linhas_historico:
                    linhas_historico.append(
                        "<tr><td colspan='4' style='text-align:center;'>"
                        "<i>Nenhum procedimento ou medicação cadastrado.</i>"
                        "</td></tr>"
                    )

                observacao_docente = (
                    self.paciente.get("observacao_docente")
                    or "Nenhuma observação registrada."
                )

                nome_usuario = (
                    self.usuario.get("name")
                    or self.usuario.get("nome")
                    or "Usuário"
                )
                papel_usuario = (
                    self.usuario.get("role")
                    or self.usuario.get("papel")
                    or "Usuário"
                )
                data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")

                graficos_html = f"""
                    <h2>2. Gráficos do monitoramento</h2>

                    <h3>2.1 Visão geral — SpO₂, Temperatura e PAM</h3>
                    <div class="grafico">
                        <img src="{caminhos_graficos['geral'].as_uri()}" />
                    </div>

                    <h3>2.2 SpO₂ — detalhamento individual</h3>
                    <p class="legenda-grafico">
                        Escala de detalhamento utilizada na interface: 70 a 100%.
                    </p>
                    <div class="grafico">
                        <img src="{caminhos_graficos['spo2'].as_uri()}" />
                    </div>

                    <h3>2.3 Temperatura — detalhamento individual</h3>
                    <p class="legenda-grafico">
                        Escala de detalhamento utilizada na interface: 34 a 42 °C.
                    </p>
                    <div class="grafico">
                        <img src="{caminhos_graficos['temperatura'].as_uri()}" />
                    </div>

                    <h3>2.4 PAM — detalhamento individual</h3>
                    <p class="legenda-grafico">
                        Escala de detalhamento utilizada na interface: 20 a 160 mmHg.
                    </p>
                    <div class="grafico">
                        <img src="{caminhos_graficos['pam'].as_uri()}" />
                    </div>
                """

                secao_ia = f"""
                    <h2>5. Análise do monitoramento com IA</h2>

                    <div class="info-box destaque-ia">
                        <b>Resumo geral</b><br>
                        {texto(getattr(relatorio, 'resumo_geral', ''))}
                    </div>

                    <h3>5.1 Evolução dos sinais</h3>
                    {lista_html(getattr(relatorio, 'evolucao_sinais', []))}

                    <h3>5.2 Eventos relevantes</h3>
                    {lista_html(getattr(relatorio, 'eventos_relevantes', []))}

                    <h3>5.3 Relações temporais</h3>
                    {lista_html(getattr(relatorio, 'relacoes_temporais', []))}

                    <h3>5.4 Informações ausentes</h3>
                    {lista_html(getattr(relatorio, 'informacoes_ausentes', []))}

                    <h3>5.5 Observações da IA</h3>
                    {lista_html(getattr(relatorio, 'observacoes', []))}

                    <div class="aviso">
                        <b>Aviso:</b><br>
                        {texto(getattr(relatorio, 'aviso', ''))}
                    </div>
                """

                conteudo_html = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            color: #1a1a1a;
                            background-color: #ffffff;
                            font-size: 10.5pt;
                        }}
                        h1 {{
                            color: {cor_tema};
                            border-bottom: 2px solid {cor_tema};
                            padding-bottom: 6px;
                            font-size: 20pt;
                        }}
                        h2 {{
                            color: {cor_tema};
                            margin-top: 22px;
                            border-bottom: 1px solid #cccccc;
                            padding-bottom: 4px;
                            font-size: 14pt;
                        }}
                        h3 {{
                            color: {cor_tema};
                            margin-top: 15px;
                            font-size: 12pt;
                        }}
                        .info-box {{
                            background-color: #f2f4f7;
                            border: 1px solid #b0bec5;
                            padding: 10px;
                            margin-bottom: 12px;
                            line-height: 1.45;
                        }}
                        .info-box b {{ color: {cor_tema}; }}
                        .destaque-ia {{
                            border-left: 4px solid {cor_tema};
                        }}
                        .grafico {{
                            text-align: center;
                            margin: 8px 0 18px 0;
                        }}
                        .grafico img {{
                            width: 100%;
                            max-width: 540px;
                            height: auto;
                        }}
                        .legenda-grafico {{
                            color: #666666;
                            font-size: 9pt;
                            margin: 0 0 5px 0;
                        }}
                        .aviso {{
                            margin-top: 14px;
                            padding: 10px;
                            border: 1px solid #d0d0d0;
                            background-color: #fffdf5;
                            font-style: italic;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 8px;
                            table-layout: fixed;
                        }}
                        th {{
                            background-color: {cor_cabecalho_tabela};
                            color: #ffffff;
                            padding: 7px;
                            text-align: left;
                        }}
                        td {{
                            padding: 7px;
                            border-bottom: 1px solid #d0d0d0;
                            word-wrap: break-word;
                        }}
                        ul {{
                            margin-top: 4px;
                            margin-bottom: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <h1>M.I.S.A. - Relatório Completo de Monitoramento com IA</h1>

                    <div class="info-box">
                        <b>Paciente:</b> {texto(self.paciente.get('nome'))} &nbsp;|&nbsp;
                        <b>Espécie:</b> {texto(self.paciente.get('especie'))} &nbsp;|&nbsp;
                        <b>Idade:</b> {texto(self.paciente.get('idade'), 0)} anos &nbsp;|&nbsp;
                        <b>Porte:</b> {texto(self.paciente.get('porte'))}<br><br>
                        <b>Responsável:</b> {texto(self.paciente.get('medico_procedimento'))}<br>
                        <b>Emitido por:</b> {texto(nome_usuario)} ({texto(papel_usuario)})<br>
                        <b>Data de emissão:</b> {texto(data_emissao)}
                    </div>

                    <h2>1. Identificação e contexto do paciente</h2>
                    <div class="info-box">
                        <b>Procedimento atual:</b> {texto(self.paciente.get('procedimento'))}<br>
                        <b>Estado clínico:</b> {texto(self.paciente.get('estado_clinico'))}<br>
                        <b>Última medicação:</b> {texto(self.paciente.get('ultima_medicacao'))}<br>
                        <b>Dose/Quantidade:</b> {texto(self.paciente.get('quantidade_medicacao'))}
                    </div>

                    {graficos_html}

                    <h2>3. Observações do docente</h2>
                    <div class="info-box">{texto(observacao_docente)}</div>

                    <h2>4. Histórico de procedimentos e medicações</h2>
                    <table>
                        <thead>
                            <tr>
                                <th width="22%">Data / Hora</th>
                                <th width="15%">Tipo</th>
                                <th width="43%">Descrição / Detalhes</th>
                                <th width="20%">Responsável</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(linhas_historico)}
                        </tbody>
                    </table>

                    {secao_ia}
                </body>
                </html>
                """

                self._atualizar_progresso_relatorio(94, "Renderizando o documento...")

                documento = QTextDocument()
                documento.setHtml(conteudo_html)

                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(caminho_arquivo)

                self._atualizar_progresso_relatorio(97, "Gravando arquivo PDF...")
                documento.print_(printer)

            self._atualizar_progresso_relatorio(100, "Relatório concluído com sucesso.")
            QCoreApplication.processEvents()
            self._fechar_progresso_relatorio()

            QMessageBox.information(
                self,
                "Relatório com IA",
                (
                    "Relatório completo gerado com sucesso!\n\n"
                    "O PDF contém:\n"
                    "• dados do paciente\n"
                    "• gráfico geral\n"
                    "• gráfico individual de SpO₂\n"
                    "• gráfico individual de Temperatura\n"
                    "• gráfico individual de PAM\n"
                    "• observações do docente\n"
                    "• histórico de procedimentos e medicações\n"
                    "• análise estruturada da IA\n\n"
                    f"Salvo em:\n{caminho_arquivo}"
                ),
            )
            return True

        except Exception as erro:
            self._fechar_progresso_relatorio()
            QMessageBox.critical(
                self,
                "Erro na geração do relatório com IA",
                f"Não foi possível gerar o PDF completo: {erro}",
            )
            return False

    def criar_card_paciente(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

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
        self.btn_editar_paciente.hide()
        self.btn_editar_paciente.clicked.connect(self.editar_paciente)
        linha_informacoes.addWidget(
            self.btn_editar_paciente,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        layout.addLayout(linha_informacoes)

        label_obs = QLabel("<b>Observações do Docente:</b>")
        label_obs.setStyleSheet(
            f"color:{cor_destaque}; font-size:13px; margin-top:4px;"
        )
        layout.addWidget(label_obs)

        self.campo_observacao = QTextEdit()
        self.campo_observacao.setMaximumHeight(58)
        self.campo_observacao.setPlaceholderText(
            "Escreva aqui observações e orientações para os alunos..."
        )
        self.campo_observacao.setStyleSheet(
            f"""
            QTextEdit {{
                border: 1px solid #c7d0d9;
                border-radius: 5px;
                padding: 6px;
                font-size: 12px;
                background-color: #ffffff;
                color: {'#287a55' if self.is_teacher else '#1a1a1a'};
            }}
            QTextEdit:focus {{
                border: 1px solid {cor_destaque};
            }}
            """
        )

        if not self.is_teacher:
            self.campo_observacao.setReadOnly(True)
            self.campo_observacao.setPlaceholderText(
                "Nenhuma observação cadastrada pelo docente."
            )

        layout.addWidget(self.campo_observacao)

        if self.is_teacher:
            self.btn_salvar_obs = QPushButton("Salvar Observação")
            self.btn_salvar_obs.setObjectName("btn_card_animal")
            self.btn_salvar_obs.setFixedHeight(28)
            self.btn_salvar_obs.clicked.connect(
                self._salvar_observacao_docente
            )
            layout.addWidget(
                self.btn_salvar_obs,
                alignment=Qt.AlignmentFlag.AlignRight,
            )

        self.cadastrar_label = QLabel("AÇÕES DO ANIMAL")
        self.cadastrar_label.setObjectName("titulo_cadastrar")
        self.cadastrar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cadastrar_label)

        linha_botoes_animais = QHBoxLayout()
        linha_botoes_animais.addStretch()

        self.btn_cadastrar = QPushButton("Cadastrar Animal")
        self.btn_cadastrar.setObjectName("btn_card_animal")
        self.btn_cadastrar.clicked.connect(self._abrir_cadastro_animal)
        self.btn_cadastrar.setVisible(self.is_teacher)
        if self.is_teacher:
            linha_botoes_animais.addWidget(self.btn_cadastrar)

        self.btn_monitorar = QPushButton("Monitorar Animal")
        self.btn_monitorar.setObjectName("btn_card_animal")
        self.btn_monitorar.clicked.connect(self._abrir_selecao_animal)
        linha_botoes_animais.addWidget(self.btn_monitorar)

        linha_botoes_animais.addStretch()
        layout.addLayout(linha_botoes_animais)

        linha_cadastro_eventos = QHBoxLayout()
        self.btn_procedimento = QPushButton("Procedimento")
        self.btn_procedimento.setObjectName("btn_card_animal")
        self.btn_procedimento.hide()
        self.btn_procedimento.clicked.connect(self.cadastrar_procedimento)

        self.btn_medicacao = QPushButton("Medicação")
        self.btn_medicacao.setObjectName("btn_card_animal")
        self.btn_medicacao.hide()
        self.btn_medicacao.clicked.connect(self.cadastrar_medicacao)

        linha_cadastro_eventos.addStretch()
        linha_cadastro_eventos.addWidget(self.btn_procedimento)
        linha_cadastro_eventos.addWidget(self.btn_medicacao)
        linha_cadastro_eventos.addStretch()
        layout.addLayout(linha_cadastro_eventos)

        # Controles do simulador mantidos da versão com IA.
        self.btn_simular_queda_spo2 = QPushButton("Queda SpO₂")
        self.btn_simular_queda_pam = QPushButton("Queda PAM")
        self.btn_simular_temperatura = QPushButton("Aumentar Temp.")
        self.btn_restaurar_sinais = QPushButton("Restaurar")

        for botao in (
            self.btn_simular_queda_spo2,
            self.btn_simular_queda_pam,
            self.btn_simular_temperatura,
            self.btn_restaurar_sinais,
        ):
            botao.setObjectName("btn_card_animal")

        self.btn_simular_queda_spo2.clicked.connect(self.simular_queda_spo2)
        self.btn_simular_queda_pam.clicked.connect(self.simular_queda_pam)
        self.btn_simular_temperatura.clicked.connect(
            self.simular_aumento_temperatura
        )
        self.btn_restaurar_sinais.clicked.connect(
            self.restaurar_sinais_teste
        )

        linha_simulacao = QHBoxLayout()
        linha_simulacao.addStretch()
        linha_simulacao.addWidget(self.btn_simular_queda_spo2)
        linha_simulacao.addWidget(self.btn_simular_queda_pam)
        linha_simulacao.addWidget(self.btn_simular_temperatura)
        linha_simulacao.addWidget(self.btn_restaurar_sinais)
        linha_simulacao.addStretch()
        layout.addLayout(linha_simulacao)

        return card

# Dentro da classe TelaInicial:

    def _salvar_observacao_docente(self) -> None:
        if not self.is_teacher:
            return

        animal_id = self.paciente.get("id")
        if not animal_id or self.paciente.get("nome") == "---":
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um animal antes de salvar observações.",
            )
            return

        texto_obs = self.campo_observacao.toPlainText().strip()

        if salvar_observacao_docente(int(animal_id), texto_obs):
            self.paciente["observacao_docente"] = texto_obs
            QMessageBox.information(
                self,
                "Sucesso",
                "Observação do docente salva com sucesso.",
            )
        else:
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível salvar a observação no banco de dados.",
            )

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

    def _carregar_animal_para_monitoramento(
        self,
        animal: dict,
        e_proprietario: bool,
    ) -> None:
        self.paciente["id"] = animal.get("id")
        self.paciente["nome"] = animal.get("nome", "---")
        self.paciente["especie"] = animal.get("especie", "---")
        self.paciente["idade"] = animal.get("idade", 0)
        self.paciente["porte"] = str(animal.get("porte", "---")).capitalize()
        self.paciente["procedimento"] = animal.get(
            "procedimento",
            "Nenhum procedimento selecionado",
        )
        self.paciente["estado_clinico"] = str(
            animal.get("estado_clinico", "---")
        ).capitalize()
        self.paciente["ultima_medicacao"] = (
            animal.get("ultima_medicacao") or "Nenhuma"
        )
        self.paciente["quantidade_medicacao"] = (
            animal.get("quantidade") or "N/A"
        )
        self.paciente["medico_procedimento"] = animal.get(
            "nome_responsavel",
            "Desconhecido",
        )
        self.paciente["observacao_docente"] = (
            animal.get("observacao_docente") or ""
        )

        responsavel_db = (
            animal.get("responsavel_aplicacao")
            or animal.get("responsavel_id")
        )
        self.paciente["responsavel_id"] = responsavel_db

        self.atualizar_informacoes_paciente()
        self.campo_observacao.setText(self.paciente["observacao_docente"])

        usuario_id = self.usuario.get("id") or self.usuario.get("usuario_id")
        try:
            e_dono = (
                int(usuario_id) == int(responsavel_db)
                if usuario_id is not None and responsavel_db is not None
                else False
            )
        except (TypeError, ValueError):
            e_dono = False

        pode_alterar = self.is_teacher or e_dono or e_proprietario

        self.btn_editar_paciente.setVisible(pode_alterar)
        self.btn_editar_paciente.setEnabled(pode_alterar)
        self.btn_procedimento.setVisible(pode_alterar)
        self.btn_procedimento.setEnabled(pode_alterar)
        self.btn_medicacao.setVisible(pode_alterar)
        self.btn_medicacao.setEnabled(pode_alterar)

        # Histórico permanente vem das tabelas oficiais do projeto.
        if self.paciente.get("id"):
            self.historico = carregar_historico_animal(
                int(self.paciente["id"])
            )
        else:
            self.historico = []
        self.atualizar_card_historico()

        # Encerra completamente o paciente/sessão anterior.
        if self.simulator is not None:
            self.simulator.stop()

        if self.id_sessao_atual is not None:
            try:
                self.repositorio_sessoes.encerrar_sessao(
                    self.id_sessao_atual
                )
            except Exception as erro:
                print(f"[M.I.S.A] Erro ao encerrar sessão anterior: {erro}")
            self.id_sessao_atual = None

        self.limpar_grafico_monitoramento()

        id_paciente = int(animal["id"])
        if usuario_id is None:
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível identificar o usuário logado.",
            )
            return

        id_sessao = self.repositorio_sessoes.iniciar_sessao(
            animal_id=id_paciente,
            usuario_id=int(usuario_id),
        )
        self.id_sessao_atual = id_sessao

        self.controlador_monitoramento.iniciar_sessao(
            id_paciente=str(id_paciente),
            id_sessao=id_sessao,
        )

        self.simulator = SinalVitalSimulacao(
            id_paciente=str(id_paciente),
            id_sessao=id_sessao,
            parent=self,
        )
        self.simulator.measurement_generated.connect(
            self.controlador_monitoramento.processar_medicoes
        )
        self.simulator.start()

        self.alerta_ia_label.setText(
            "<b>Monitoramento iniciado.</b><br>"
            "Analisando os sinais vitais do paciente em tempo real."
        )

        if not pode_alterar:
            QMessageBox.information(
                self,
                "Modo Somente Leitura",
                (
                    "Você está monitorando o paciente de "
                    f"{animal.get('nome_responsavel', 'outro usuário')}.\n\n"
                    "Edição, procedimentos e medicações permanecem bloqueados."
                ),
            )

    def atualizar_informacoes_paciente(self) -> None:
        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

        self.informacoes_paciente.setText(
            f"<span style='color:{cor_destaque};'><b>Nome:</b></span> "
            f"{self.paciente['nome']}<br>"
            f"<span style='color:{cor_destaque};'><b>Espécie:</b></span> "
            f"{self.paciente['especie']}<br>"
            f"<span style='color:{cor_destaque};'><b>Idade:</b></span> "
            f"{self.paciente['idade']} anos<br>"
            f"<span style='color:{cor_destaque};'><b>Porte:</b></span> "
            f"{self.paciente['porte']}<br><br>"
            f"<span style='color:{cor_destaque};'><b>Responsável:</b></span> "
            f"{self.paciente['medico_procedimento']}<br>"
            f"<span style='color:{cor_destaque};'><b>Procedimento:</b></span> "
            f"{self.paciente['procedimento']}<br>"
            f"<span style='color:{cor_destaque};'><b>Estado Clínico:</b></span> "
            f"{self.paciente['estado_clinico']}<br>"
            f"<span style='color:{cor_destaque};'><b>Última Medicação:</b></span> "
            f"{self.paciente['ultima_medicacao']} "
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
        layout.setSpacing(6)

        self.historico_container = QWidget()
        self.historico_container.setStyleSheet("background-color: #ffffff;")
        self.historico_layout = QVBoxLayout(self.historico_container)
        self.historico_layout.setContentsMargins(0, 0, 0, 0)
        self.historico_layout.setSpacing(6)
        self.historico_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.historico_container)
        scroll_area.setStyleSheet(
            """
            QScrollArea, QScrollArea > QWidget > QWidget {
                background-color: #ffffff;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            """
        )
        layout.addWidget(scroll_area, 1)

        rodape = QHBoxLayout()
        rodape.setContentsMargins(0, 4, 0, 0)

        self.btn_pdf_historico = QPushButton("📄 Baixar PDF")
        self.btn_pdf_historico.setObjectName("btn_card_animal")
        self.btn_pdf_historico.setToolTip(
            "Exportar gráfico, histórico e relatório já gerado pela IA"
        )
        self.btn_pdf_historico.clicked.connect(
            lambda: self.exportar_relatorio_pdf()
        )
        rodape.addWidget(
            self.btn_pdf_historico,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        rodape.addStretch()

        ver_mais = QPushButton("Ver Mais")
        ver_mais.setObjectName("botao_ver_mais")
        ver_mais.clicked.connect(self.ver_historico_completo)
        rodape.addWidget(
            ver_mais,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        layout.addLayout(rodape)
        self.atualizar_card_historico()
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
        if self.paciente.get("nome") == "---" or not self.paciente.get("id"):
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um animal para lançar procedimentos.",
            )
            return

        dialogo = CadastrarProcedimentoDialog(self.paciente, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        dados = dialogo.dados()
        usuario_id = self.usuario.get("id") or self.usuario.get("usuario_id")
        if usuario_id is None:
            QMessageBox.critical(self, "Erro", "Usuário logado sem ID.")
            return

        try:
            data_hora = self._converter_data_hora_registro(
                dados.get("data"),
                dados.get("hora"),
            )
        except (TypeError, ValueError):
            data_hora = datetime.now()

        observacao = dados.get("observacao")
        responsavel_informado = dados.get("medico_procedimento")
        nome_usuario = self.usuario.get("name") or self.usuario.get("nome")
        if responsavel_informado and responsavel_informado != nome_usuario:
            complemento = (
                "Responsável informado no lançamento: "
                f"{responsavel_informado}"
            )
            observacao = (
                f"{observacao}\n{complemento}" if observacao else complemento
            )

        sucesso = salvar_historico_procedimento(
            animal_id=int(self.paciente["id"]),
            realizado_por=int(usuario_id),
            registrado_por=int(usuario_id),
            procedimento=dados["procedimento"],
            descricao_detalhada=observacao,
            sessao_id=self.id_sessao_atual,
            data_hora=data_hora,
        )

        if not sucesso:
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível salvar o procedimento no banco de dados.",
            )
            return

        self.historico = carregar_historico_animal(
            int(self.paciente["id"])
        )
        self.paciente["procedimento"] = dados["procedimento"]
        self.paciente["medico_procedimento"] = (
            dados.get("medico_procedimento")
            or self.paciente.get("medico_procedimento")
        )
        self.atualizar_informacoes_paciente()
        self.atualizar_card_historico()

    def cadastrar_medicacao(self) -> None:
        if self.paciente.get("nome") == "---" or not self.paciente.get("id"):
            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um animal para lançar medicações.",
            )
            return

        dialogo = CadastrarMedicacaoDialog(self.paciente, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        dados = dialogo.dados()
        usuario_id = self.usuario.get("id") or self.usuario.get("usuario_id")
        if usuario_id is None:
            QMessageBox.critical(self, "Erro", "Usuário logado sem ID.")
            return

        try:
            quantidade = float(str(dados["quantidade"]).replace(",", "."))
        except (TypeError, ValueError):
            quantidade = None

        unidade = str(dados.get("unidade") or "").strip() or None
        dose_quantidade = (
            f"{dados.get('quantidade', '')} {unidade or ''}"
        ).strip()

        try:
            data_hora = self._converter_data_hora_registro(
                dados.get("data"),
                dados.get("hora"),
            )
        except (TypeError, ValueError):
            data_hora = datetime.now()

        observacao = dados.get("observacao")
        responsavel_informado = dados.get("medico_medicacao")
        nome_usuario = self.usuario.get("name") or self.usuario.get("nome")
        if responsavel_informado and responsavel_informado != nome_usuario:
            complemento = (
                "Responsável informado no lançamento: "
                f"{responsavel_informado}"
            )
            observacao = (
                f"{observacao}\n{complemento}" if observacao else complemento
            )

        sucesso = salvar_historico_medicacao(
            animal_id=int(self.paciente["id"]),
            administrado_por=int(usuario_id),
            registrado_por=int(usuario_id),
            medicamento=dados["medicacao"],
            dose_quantidade=dose_quantidade or "Não informado",
            quantidade=quantidade,
            unidade=unidade,
            via_administracao=dados.get("via_administracao"),
            observacao=observacao,
            sessao_id=self.id_sessao_atual,
            data_hora=data_hora,
        )

        if not sucesso:
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível salvar a medicação no banco de dados.",
            )
            return

        self.historico = carregar_historico_animal(
            int(self.paciente["id"])
        )
        self.paciente["ultima_medicacao"] = dados["medicacao"]
        self.paciente["quantidade_medicacao"] = dose_quantidade or "N/A"
        self.atualizar_informacoes_paciente()
        self.atualizar_card_historico()

    def ver_historico_completo(self) -> None:
        dialogo = HistoricoDialog(self.historico, self)
        dialogo.exec()

    def atualizar_card_historico(self) -> None:
        while self.historico_layout.count() > 0:
            item = self.historico_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not self.historico:
            vazio = QLabel(
                "<i>Nenhum procedimento ou medicação cadastrado.</i>"
            )
            vazio.setStyleSheet(
                "color:#666666; font-size:13px; background-color:#ffffff;"
            )
            self.historico_layout.addWidget(vazio)
            return

        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

        for registro in self.historico[:10]:
            item_widget = QWidget()
            item_widget.setStyleSheet("background-color:#ffffff;")
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 2, 4, 6)
            item_layout.setSpacing(6)

            if registro.get("tipo") == "Procedimento":
                texto_html = (
                    f"<span style='color:{cor_destaque};'><b>Procedimento:</b></span> "
                    f"{registro.get('procedimento', '---')}<br>"
                    f"<span style='color:{cor_destaque};'><b>Responsável:</b></span> "
                    f"{registro.get('medico_procedimento', '---')}<br>"
                    f"<small style='color:#666666;'>Data: {registro.get('data', '')} | "
                    f"Hora: {registro.get('hora', '')}</small>"
                )
            else:
                dose = registro.get("quantidade") or "Não informada"
                via = registro.get("via_administracao")
                texto_html = (
                    f"<span style='color:{cor_destaque};'><b>Medicação:</b></span> "
                    f"{registro.get('medicacao', '---')} ({dose})<br>"
                    f"<span style='color:{cor_destaque};'><b>Responsável:</b></span> "
                    f"{registro.get('medico_medicacao', '---')}"
                )
                if via:
                    texto_html += f"<br><b>Via:</b> {via}"
                texto_html += (
                    f"<br><small style='color:#666666;'>Data: {registro.get('data', '')} | "
                    f"Hora: {registro.get('hora', '')}</small>"
                )

            lbl_info = QLabel(texto_html)
            lbl_info.setTextFormat(Qt.TextFormat.RichText)
            lbl_info.setWordWrap(True)
            lbl_info.setStyleSheet(
                "color:#1a1a1a; font-size:13px; background-color:transparent;"
            )
            item_layout.addWidget(lbl_info, 1)

            if self.is_teacher:
                btn_excluir = QPushButton("✕")
                btn_excluir.setToolTip("Excluir este registro do histórico")
                btn_excluir.setFixedSize(22, 22)
                btn_excluir.setStyleSheet(
                    """
                    QPushButton {
                        color: #d9534f;
                        background-color: transparent;
                        border: none;
                        font-weight: bold;
                        font-size: 14px;
                        border-radius: 11px;
                    }
                    QPushButton:hover {
                        background-color: #fde8e8;
                        color: #c9302c;
                    }
                    """
                )
                btn_excluir.clicked.connect(
                    lambda _, reg=registro: self._excluir_item_historico(reg)
                )
                item_layout.addWidget(
                    btn_excluir,
                    alignment=Qt.AlignmentFlag.AlignTop,
                )

            self.historico_layout.addWidget(item_widget)

            linha = QFrame()
            linha.setFrameShape(QFrame.Shape.HLine)
            linha.setStyleSheet(
                "color:#e0e0e0; background-color:#e0e0e0; max-height:1px;"
            )
            self.historico_layout.addWidget(linha)

    def _excluir_item_historico(self, registro: dict) -> None:
        if not self.is_teacher:
            return

        tipo = registro.get("tipo", "Registro")
        confirmacao = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir este lançamento de {tipo}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmacao != QMessageBox.StandardButton.Yes:
            return

        registro_id = registro.get("id")
        if registro_id is None:
            return

        if tipo == "Procedimento":
            sucesso = deletar_historico_procedimento(int(registro_id))
        else:
            sucesso = deletar_historico_medicacao(int(registro_id))

        if not sucesso:
            QMessageBox.critical(
                self,
                "Erro",
                f"Não foi possível excluir o lançamento de {tipo}.",
            )
            return

        animal_id = self.paciente.get("id")
        self.historico = (
            carregar_historico_animal(int(animal_id))
            if animal_id
            else []
        )
        self.atualizar_card_historico()

    def _aplicar_estilos(self) -> None:
        cor_tema = "#287a55" if self.is_teacher else "#08b9df"
        cor_hover = "#216746" if self.is_teacher else "#078eaa"
        cor_secundaria = "#1f4d3a" if self.is_teacher else "#2100b8"

        self.setStyleSheet(
            f"""
            #cabecalho {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
            }}
            #cabecalho QLabel {{
                font-size: 14px;
                color: #333333;
            }}
            #botao_menu {{
                background-color: transparent;
                color: {cor_tema};
                border: none;
                font-size: 26px;
                font-weight: bold;
            }}
            #botao_menu:hover {{ color: {cor_hover}; }}

            #layout_fundo {{ background-color: {cor_tema}; }}

            #card {{
                background-color: white;
                border: none;
                border-radius: 10px;
            }}

            #titulo_secao {{
                color: white;
                font-size: 16px;
                font-weight: bold;
            }}

            #card QLabel {{ color: black; font-size: 14px; }}
            #card QLabel b {{ color: {cor_tema}; }}

            #botao_acao {{
                color: {cor_tema};
                background-color: transparent;
                border: none;
                font-weight: bold;
            }}
            #botao_acao:hover {{ color: {cor_hover}; }}

            #botao_ver_mais {{
                color: {cor_secundaria};
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }}

            #titulo_cadastrar {{
                color: {cor_secundaria};
                font-size: 14px;
                font-weight: bold;
            }}

            #btn_card_animal {{
                background-color: {cor_tema};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: 600;
                font-size: 12px;
            }}
            #btn_card_animal:hover {{ background-color: {cor_hover}; }}
            #btn_card_animal:disabled {{
                background-color: #b9c2c8;
                color: #f7f7f7;
            }}

            QPushButton#card_sinal {{
                background-color: #f7f9fb;
                color: #242424;
                border: 2px solid #e4e8ec;
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }}

            QPushButton#card_sinal:hover {{
                background-color: #f0fbfd;
                border: 2px solid {cor_tema};
            }}

            QPushButton#card_sinal:checked {{
                background-color: #eef0ff;
                border: 2px solid {cor_secundaria};
                color: {cor_secundaria};
            }}
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

            minimo_amostras = 6
            amostras_por_parametro = {}

            for parametro, analise in analises.items():
                quantidade = analise.get("amostras", minimo_amostras)
                amostras_por_parametro[parametro] = min(
                    quantidade,
                    minimo_amostras,
                )

            amostras_spo2 = amostras_por_parametro.get(
                ParametroVital.SPO2,
                0,
            )
            amostras_temperatura = amostras_por_parametro.get(
                ParametroVital.TEMPERATURA,
                0,
            )
            amostras_pam = amostras_por_parametro.get(
                ParametroVital.PRESSAO_ARTERIAL_MEDIA,
                0,
            )
            progresso_geral = min(
                amostras_spo2,
                amostras_temperatura,
                amostras_pam,
            )

            self._aplicar_estilo_alerta("indisponivel")

            self.alerta_ia_label.setText(
                (
                    "<span style='font-size:17px;'>"
                    "<b>◷ Inicializando monitoramento</b>"
                    "</span>"
                    "<br><br>"
                    "O sistema está coletando dados para estabelecer "
                    "a referência recente do paciente."
                    "<br><br>"
                    "<b>Progresso da coleta:</b> "
                    f"{progresso_geral}/{minimo_amostras} leituras"
                    "<br><br>"
                    f"SpO₂: <b>{amostras_spo2}/6</b><br>"
                    f"Temperatura: <b>{amostras_temperatura}/6</b><br>"
                    f"PAM: <b>{amostras_pam}/6</b>"
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

    def _abrir_progresso_relatorio(self) -> None:
        """Exibe uma janela modal com o progresso da geração do relatório IA."""
        self._fechar_progresso_relatorio()

        dialogo = QProgressDialog(
            "Preparando geração do relatório...",
            "",
            0,
            100,
            self,
        )
        dialogo.setWindowTitle("Gerando Relatório com IA")
        dialogo.setCancelButton(None)
        dialogo.setWindowModality(Qt.WindowModality.WindowModal)
        dialogo.setMinimumDuration(0)
        dialogo.setAutoClose(False)
        dialogo.setAutoReset(False)
        dialogo.setValue(0)
        dialogo.resize(430, 120)

        cor_tema = "#287a55" if self.is_teacher else "#08b9df"
        dialogo.setStyleSheet(
            f"""
            QProgressDialog {{
                background-color: #ffffff;
                color: #222222;
                min-width: 420px;
            }}
            QLabel {{
                color: #333333;
                font-size: 13px;
                padding: 8px 4px;
            }}
            QProgressBar {{
                border: 1px solid #c7d0d9;
                border-radius: 7px;
                background-color: #f1f3f5;
                color: #222222;
                text-align: center;
                min-height: 22px;
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {cor_tema};
                border-radius: 6px;
            }}
            """
        )

        self.dialogo_progresso_relatorio = dialogo
        dialogo.show()
        QCoreApplication.processEvents()

    def _atualizar_progresso_relatorio(
        self,
        valor: int,
        mensagem: str,
    ) -> None:
        """Atualiza porcentagem e descrição da etapa atual do relatório."""
        dialogo = self.dialogo_progresso_relatorio
        if dialogo is None:
            return

        valor = max(0, min(100, int(valor)))
        dialogo.setLabelText(mensagem)
        dialogo.setValue(valor)
        QCoreApplication.processEvents()

    def _fechar_progresso_relatorio(self) -> None:
        dialogo = self.dialogo_progresso_relatorio
        if dialogo is not None:
            dialogo.close()
            dialogo.deleteLater()
            self.dialogo_progresso_relatorio = None

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

        nome_seguro = (
            str(self.paciente.get("nome", "paciente")).strip() or "paciente"
        )
        nome_sugerido = f"Relatorio_MISA_IA_{nome_seguro}.pdf"
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório Completo com IA",
            nome_sugerido,
            "Arquivos PDF (*.pdf)",
        )

        if not caminho_arquivo:
            return

        if not caminho_arquivo.lower().endswith(".pdf"):
            caminho_arquivo += ".pdf"

        self.caminho_relatorio_ia_pendente = caminho_arquivo

        # Fecha o menu lateral e exibe o progresso antes de iniciar a IA.
        self.fechar_menu()
        self._abrir_progresso_relatorio()
        self._atualizar_progresso_relatorio(5, "Preparando dados da sessão...")

        self.btn_relatorio.setEnabled(False)
        self.btn_relatorio.setText("Gerando relatório...")

        self.thread_relatorio = QThread(self)

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

        self._atualizar_progresso_relatorio(15, "Analisando monitoramento com a IA...")
        self.thread_relatorio.start()

    def _relatorio_gerado(self, relatorio) -> None:
        self.relatorio_ia_atual = relatorio

        print()
        print("[M.I.S.A] Relatório por IA gerado.")
        print(relatorio.resumo_geral)

        self._atualizar_progresso_relatorio(55, "Análise da IA concluída.")

        # O botão lateral gera o relatório completo: conteúdo clínico,
        # histórico, quatro gráficos e análise estruturada pela IA.
        self.exportar_relatorio_completo_ia(
            self.caminho_relatorio_ia_pendente
        )

    def _erro_geracao_relatorio(
        self,
        mensagem: str,
    ) -> None:

        self._fechar_progresso_relatorio()
        self.caminho_relatorio_ia_pendente = None

        QMessageBox.critical(
            self,
            "Erro ao gerar relatório",
            (
                "Não foi possível gerar "
                "o relatório por IA.\n\n"
                f"{mensagem}"
            ),
        )

    def _finalizar_geracao_relatorio(self) -> None:
        self.btn_relatorio.setEnabled(True)
        self.btn_relatorio.setText("Relatório com IA")

        # Em caso de encerramento antecipado, garante que a janela de progresso
        # não permaneça aberta. Em sucesso ela já terá sido fechada ao chegar a 100%.
        self._fechar_progresso_relatorio()
        self.caminho_relatorio_ia_pendente = None

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
