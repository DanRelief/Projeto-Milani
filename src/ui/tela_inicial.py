from pathlib import Path
from uuid import uuid4

from src.infrastructure.database import salvar_observacao_docente

from ..infrastructure.database import (
    carregar_historico_animal,
    salvar_historico_medicacao,
    salvar_historico_procedimento,
)

from PySide6.QtPrintSupport import QPrinter

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QTextDocument
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
    QTextEdit,
    QFileDialog
)
from PySide6.QtCharts import QCategoryAxis, QChart, QChartView, QSplineSeries, QValueAxis

from ..infrastructure.simulation.sinais_vitais_simulacao import SinalVitalSimulacao
from .dialogs.editar_paciente_dialog import EditarPacienteDialog
from .dialogs.procedimento_dialog import CadastrarProcedimentoDialog
from .dialogs.medicacao_dialog import CadastrarMedicacaoDialog
from .dialogs.historico_ver_mais_dialog import HistoricoDialog

from .cadastrar_animal import DialogCadastrarAnimal
from .selecionar_animal import DialogSelecionarAnimal

from src.infrastructure.database import criar_sessao_monitoramento, salvar_medicao_sinal_vital

class TelaInicial(QMainWindow):
    logout_requested = Signal()

    def __init__(self, usuario: dict[str, str]) -> None:
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("M.I.S.A - Tela Inicial")
        self.resize(1024, 720)
        self.setMinimumSize(900, 650)

        # 1. Definição ÚNICA e padronizada do papel do usuário
        user_role = str(usuario.get("role", "")).strip().lower()
        self.is_teacher = user_role in ["teacher", "docente", "professor", "admin"]

        # 2. Inicialmente sem animal selecionado (dados zerados)
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
        }

        self.sessao_ativa_id = None  # Armazena o UUID da sessão em sessoes_monitoramento
        self.historico = []
        self.simulator = None

        # Widget Central e Layout Principal
        central = QWidget()
        central.setObjectName("layout_fundo")
        layout_fundo = QVBoxLayout(central)
        layout_fundo.setContentsMargins(0, 0, 0, 0)
        layout_fundo.setSpacing(0)

        # Cabeçalho Superior
        cabecalho = QWidget()
        cabecalho.setObjectName("cabecalho")
        cabecalho.setFixedHeight(75)
        layout_cabecalho = QHBoxLayout(cabecalho)
        layout_cabecalho.setContentsMargins(16, 0, 16, 0)
        layout_cabecalho.setSpacing(16)

        # 3. Busca dinamicamente e com segurança o diretório de assets
        # Tenta localizar a pasta assets subindo na árvore de diretórios
        diretorio_atual = Path(__file__).resolve().parent
        pasta_assets = None
        for pai in [diretorio_atual] + list(diretorio_atual.parents):
            candidato = pai / "assets"
            if candidato.is_dir():
                pasta_assets = candidato
                break

        if not pasta_assets:
            pasta_assets = Path(__file__).resolve().parents[2] / "assets"

        # 4. Seleção flexível do arquivo de imagem do logo do Docente
        caminho_logo = None
        if self.is_teacher:
            for nome_arquivo in ["logo_misa_docente.jpg", "logo_misa_docente.png", "logo_misa_verde.png"]:
                teste = pasta_assets / nome_arquivo
                if teste.exists():
                    caminho_logo = teste
                    break

        # Fallback para o logo do Aluno
        if not caminho_logo or not caminho_logo.exists():
            caminho_logo = pasta_assets / "logo_misa.png"

        logo = QLabel()
        pixmap = QPixmap(str(caminho_logo))
        
        # Só exibe se o PySide6 conseguir carregar o Pixmap com sucesso
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    200,
                    70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # 5. Definição da cor do tema do cabeçalho
        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

        dados_usuario = QLabel(
            f'<span style="color:{cor_destaque};"><b>{usuario.get("role", "Aluno")}:</b></span> '
            f'{usuario.get("name", "")}<br>'
            f'<span style="color:{cor_destaque};"><b>{usuario.get("identifier_label", "E-mail")}:</b></span> '
            f'{usuario.get("identifier", "")}'
        )

        nome_professor = usuario.get("professor_name", "Milani")
        dados_professor = QLabel(
            f'<span style="color:{cor_destaque};"><b>Professor:</b></span> {nome_professor}'
        )

        # Botão do Menu Lateral (☰)
        botao_menu = QPushButton("\u2630")
        botao_menu.setObjectName("botao_menu")
        botao_menu.clicked.connect(self.alternar_menu)

        # Título M.I.S.A.
        titulo = QLabel("M.I.S.A")
        titulo.setStyleSheet(f"font-size: 38px; font-weight: bold; color: {cor_destaque};")

        # Adiciona os elementos ao layout do cabeçalho
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

        # Aplica os estilos gerais e constrói o menu lateral
        self._aplicar_estilos()
        self.setCentralWidget(central)
        self.montar_menu_lateral(central, usuario)

    def update_chart(self, medicao) -> None:
        primeira_serie = self.series_map["freq_cardiaca"][0]
        index = primeira_serie.count()

        valores = {
            "oxigenio": (getattr(medicao, "oxigenio", getattr(medicao, "spo2", 0.0)), "%"),
            "pressao_arterial": (getattr(medicao, "pressao_arterial", 0.0), "mmHg"),
            "temperatura": (getattr(medicao, "temperatura", 0.0), "°C"),
        }

        # Atualiza a interface gráfica
        for key, (val, und) in valores.items():
            if key in self.series_map:
                series = self.series_map[key][0]
                series.append(float(index), float(val))

            # Se houver uma sessão ativa, persiste as medições no MySQL
            if self.sessao_ativa_id:
                salvar_medicao_sinal_vital(
                    sessao_id=self.sessao_ativa_id,
                    parametro=key,
                    valor=float(val),
                    unidade=und,
                    fonte="simulador"
                )

        # Ajuste do eixo X do gráfico
        JANELA_MAXIMA = 30
        if index >= JANELA_MAXIMA:
            self.axis_x.setRange(index - JANELA_MAXIMA + 1, index)
        else:
            self.axis_x.setRange(0, JANELA_MAXIMA)

    def montar_menu_lateral(
        self, central: QWidget, usuario: dict[str, str]
    ) -> None:
        """Cria o painel lateral sobreposto à tela inicial com cores dinâmicas por perfil."""
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
        if caminho_logo.exists():
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

        # 1. Define as cores dinâmicas de acordo com o papel do usuário logado:
        # - Verde para Docente (#287a55) / Hover (#216746)
        # - Azul para Aluno (#08b9df) / Hover (#078eaa)
        e_docente = getattr(self, "is_teacher", False) or str(usuario.get("role", "")).lower() in ["teacher", "docente", "professor"]
        
        cor_tema = "#287a55" if e_docente else "#08b9df"
        cor_hover_item = "#216746" if e_docente else "#078eaa"
        cor_fechar_bg = "#1f4d3a" if e_docente else "#2100b8"
        cor_fechar_hover = "#183e2e" if e_docente else "#351bc9"

        # 2. Aplica o estilo dinâmico diretamente na gaveta do menu lateral
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
                background-color: {cor_fechar_bg};
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
                color: {cor_hover_item};
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

        card_paciente.setFixedHeight(480)
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

    def exportar_relatorio_pdf(self) -> None:
        if self.paciente.get("nome") == "---":
            QMessageBox.warning(
                self, "Aviso", "Selecione um animal antes de exportar o relatório."
            )
            return

        # 1. Abre a caixa de diálogo para o aluno escolher a pasta onde salvar
        nome_sugerido = f"Relatorio_MISA_{self.paciente['nome']}.pdf"
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório em PDF", nome_sugerido, "Arquivos PDF (*.pdf)"
        )

        if not caminho_arquivo:
            return  # Aluno cancelou a caixa de diálogo

        if not caminho_arquivo.endswith(".pdf"):
            caminho_arquivo += ".pdf"

        try:
            # 2. Captura a imagem do gráfico atual
            pixmap_grafico = self.grafico_view.grab()
            # Salva temporariamente a imagem como PNG em memória base64 ou pasta temporária
            caminho_img_temp = "temp_grafico_misa.png"
            pixmap_grafico.save(caminho_img_temp, "PNG")

            # 3. Monta o histórico formatado em tabela HTML
            linhas_historico_html = ""
            if not self.historico:
                linhas_historico_html = "<tr><td colspan='4'>Nenhum procedimento ou medicação cadastrada até o momento.</td></tr>"
            else:
                for reg in self.historico:
                    data_hora = f"{reg.get('data', '')} {reg.get('hora', '')}".strip()
                    if reg.get("tipo") == "Procedimento":
                        detalhe = f"Procedimento: {reg.get('procedimento', '-')}"
                        resp = reg.get("medico_procedimento", "-")
                    else:
                        detalhe = f"Medicação: {reg.get('medicacao', '-')} (Qtd: {reg.get('quantidade', '')} {reg.get('unidade', '')})"
                        resp = reg.get("medico_medicacao", "-")

                    linhas_historico_html += f"""
                        <tr>
                            <td style='padding: 6px; border-bottom: 1px solid #ddd;'>{data_hora}</td>
                            <td style='padding: 6px; border-bottom: 1px solid #ddd;'><b>{reg.get('tipo', 'Registro')}</b></td>
                            <td style='padding: 6px; border-bottom: 1px solid #ddd;'>{detalhe}</td>
                            <td style='padding: 6px; border-bottom: 1px solid #ddd;'>{resp}</td>
                        </tr>
                    """

            # 4. Estrutura o HTML Completo do Relatório
            observacao = self.paciente.get("observacao_docente") or "Nenhuma observação registrada."
            
            conteudo_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #1a1a1a; }}
                    h1 {{ color: #08b9df; border-bottom: 2px solid #08b9df; padding-bottom: 5px; }}
                    h2 {{ color: #1f4d3a; margin-top: 20px; font-size: 16px; }}
                    .info-box {{ background-color: #f7f9fc; border: 1px solid #c7d0d9; padding: 12px; border-radius: 5px; margin-bottom: 15px; }}
                    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }}
                    th {{ background-color: #287a55; color: white; padding: 8px; text-align: left; }}
                </style>
            </head>
            <body>
                <h1>M.I.S.A. - Relatório de Monitoramento Animal</h1>
                
                <div class="info-box">
                    <b>Paciente:</b> {self.paciente['nome']} &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <b>Espécie:</b> {self.paciente['especie']} &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <b>Idade:</b> {self.paciente['idade']} anos &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <b>Porte:</b> {self.paciente['porte']}<br>
                    <b>Responsável:</b> {self.paciente['medico_procedimento']}<br>
                    <b>Emitido por:</b> {self.usuario.get('name', 'Aluno')} ({self.usuario.get('role', 'Aluno')})
                </div>

                <h2>1. Gráfico de Sinais Vitais em Tempo Real</h2>
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="{caminho_img_temp}" width="600" />
                </div>

                <h2>2. Observações do Docente</h2>
                <div class="info-box">
                    <i>{observacao}</i>
                </div>

                <h2>3. Histórico de Procedimentos e Medicações</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Data / Hora</th>
                            <th>Tipo</th>
                            <th>Descrição / Detalhes</th>
                            <th>Responsável</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_historico_html}
                    </tbody>
                </table>
            </body>
            </html>
            """

            # 5. Renderiza e Imprime o Documento no Arquivo PDF
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

        except Exception as err:
            QMessageBox.critical(
                self, "Erro na Geracao", f"Não foi possível gerar o PDF: {err}"
            )

    def criar_card_paciente(self) -> QFrame:
        card = self.criar_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Recupera e valida se o usuário logado é Docente (Teacher)
        user_role = str(self.usuario.get("role", "")).strip().lower()
        self.is_teacher = user_role in ["teacher", "docente", "professor", "admin"]
        cor_destaque = "#287a55" if self.is_teacher else "#08b9df"

        # 2. Informações básicas do Paciente
        self.informacoes_paciente = QLabel()
        self.informacoes_paciente.setObjectName("informacoes_paciente")
        self.informacoes_paciente.setTextFormat(Qt.TextFormat.RichText)
        self.informacoes_paciente.setStyleSheet("font-size: 14px;")
        self.atualizar_informacoes_paciente()

        linha_informacoes = QHBoxLayout()
        linha_informacoes.setContentsMargins(0, 0, 0, 0)
        linha_informacoes.addWidget(self.informacoes_paciente, 1)

        # Botão Editar
        self.btn_editar_paciente = QPushButton("Editar")
        self.btn_editar_paciente.setObjectName("botao_acao")
        self.btn_editar_paciente.hide()  # Oculto inicialmente até selecionar paciente
        self.btn_editar_paciente.clicked.connect(self.editar_paciente)
        linha_informacoes.addWidget(
            self.btn_editar_paciente,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        layout.addLayout(linha_informacoes)

        # 3. Rótulo de Observações do Docente
        label_obs = QLabel("<b>Observações do Docente:</b>")
        label_obs.setStyleSheet(f"color: {cor_destaque}; font-size: 13px; margin-top: 6px;")
        layout.addWidget(label_obs)

        # 4. INSTANCIAÇÃO DA CAIXA DE TEXTO (Precisa vir ANTES de usar setStyleSheet ou atribuir estilos)
        self.campo_observacao = QTextEdit()
        self.campo_observacao.setPlaceholderText("Escreva aqui observações e orientações para os alunos...")
        self.campo_observacao.setMaximumHeight(60)

        # Cor do texto de observação: Verde para Docente, Escuro/Preto para Aluno
        cor_texto_box = "#287a55" if self.is_teacher else "#1a1a1a"

        self.campo_observacao.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid #c7d0d9;
                border-radius: 5px;
                padding: 6px;
                font-size: 12px;
                background-color: #ffffff;
                color: {cor_texto_box};
            }}
            QTextEdit:focus {{
                border: 1px solid {cor_destaque};
            }}
        """)

        # Se for Aluno, a caixa fica em modo somente leitura
        if not self.is_teacher:
            self.campo_observacao.setReadOnly(True)
            self.campo_observacao.setPlaceholderText("Nenhuma observação cadastrada pelo docente.")

        layout.addWidget(self.campo_observacao)

        # Botão para o Docente Salvar as Observações
        if self.is_teacher:
            self.btn_salvar_obs = QPushButton("Salvar Observação")
            self.btn_salvar_obs.setObjectName("btn_card_animal")
            self.btn_salvar_obs.setFixedHeight(28)
            self.btn_salvar_obs.clicked.connect(self._salvar_observacao_docente)
            layout.addWidget(self.btn_salvar_obs, alignment=Qt.AlignmentFlag.AlignRight)

        # 5. Seção AÇÕES DO ANIMAL
        self.cadastrar_label = QLabel("")
        self.cadastrar_label.setObjectName("titulo_cadastrar")
        self.cadastrar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cadastrar_label.hide()
        layout.addWidget(self.cadastrar_label)

        # Botões de Gestão (Cadastrar / Monitorar)
        linha_botoes_animais = QHBoxLayout()
        linha_botoes_animais.addStretch()

        self.btn_cadastrar = QPushButton("Cadastrar Animal")
        self.btn_cadastrar.setObjectName("btn_card_animal")
        self.btn_cadastrar.clicked.connect(self._abrir_cadastro_animal)
        
        if self.is_teacher:
            self.btn_cadastrar.show()
            linha_botoes_animais.addWidget(self.btn_cadastrar)
        else:
            self.btn_cadastrar.hide()

        self.btn_monitorar = QPushButton("Monitorar Animal")
        self.btn_monitorar.setObjectName("btn_card_animal")
        self.btn_monitorar.clicked.connect(self._abrir_selecao_animal)
        linha_botoes_animais.addWidget(self.btn_monitorar)

        linha_botoes_animais.addStretch()
        layout.addLayout(linha_botoes_animais)

        # Botões Lançamentos Clínicos (Procedimento / Medicação)
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

        return card

    def _salvar_observacao_docente(self) -> None:
        animal_id = self.paciente.get("id")
        if not animal_id or self.paciente.get("nome") == "---":
            QMessageBox.warning(self, "Aviso", "Selecione um animal antes de salvar observações.")
            return

        texto_obs = self.campo_observacao.toPlainText().strip()
        
        # Persiste diretamente na tabela 'animais' do MySQL
        if salvar_observacao_docente(animal_id, texto_obs):
            self.paciente["observacao_docente"] = texto_obs
            QMessageBox.information(self, "Sucesso", "Observação registrada e salva no banco de dados com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar a observação no banco de dados.")

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

        mapa_series = {
        "spo2": "spo2",
        "temperatura": "temperatura",
        "pressao_arterial_media": "pressao_arterial",
        }

        for medicoes in medicao:
            chave = mapa_series.get(medicoes.parametro.value)

            if chave is None:
                continue

            self.series_map[chave][0].append(
                index,
                float(medicoes.valor),
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
        """Carrega os dados do animal selecionado no diálogo para monitoramento na tela inicial."""
        # 1. Atualiza o dicionário local do paciente com os dados do MySQL
        self.paciente["id"] = animal.get("id")
        self.paciente["nome"] = animal.get("nome", "---")
        self.paciente["especie"] = animal.get("especie", "---")
        self.paciente["idade"] = animal.get("idade", 0)
        self.paciente["porte"] = str(animal.get("porte", "---")).capitalize()
        self.paciente["procedimento"] = animal.get("procedimento", "Nenhum procedimento selecionado")
        self.paciente["estado_clinico"] = str(animal.get("estado_clinico", "---")).capitalize()
        self.paciente["ultima_medicacao"] = animal.get("ultima_medicacao") or "Nenhuma"
        self.paciente["quantidade_medicacao"] = animal.get("quantidade") or "N/A"
        self.paciente["medico_procedimento"] = animal.get("nome_responsavel", "Desconhecido")
        self.paciente["observacao_docente"] = animal.get("observacao_docente") or ""

        responsavel_db = animal.get("responsavel_aplicacao") or animal.get("responsavel_id")
        self.paciente["responsavel_id"] = responsavel_db

        # Atualiza as informações visuais na interface
        self.atualizar_informacoes_paciente()

        # Atualiza a caixa de observação se ela existir na interface
        if hasattr(self, "campo_observacao"):
            self.campo_observacao.setText(self.paciente["observacao_docente"])

        # 2. Recupera o ID do usuário logado
        user_id_logado = self.usuario.get("id") or self.usuario.get("usuario_id")

        # 3. Compara se o usuário logado é o responsável pelo animal
        try:
            e_dono = (int(user_id_logado) == int(responsavel_db)) if (user_id_logado and responsavel_db) else False
        except (ValueError, TypeError):
            e_dono = False

        # O aluno pode alterar apenas se for o dono. O docente pode alterar qualquer paciente.
        pode_alterar = getattr(self, "is_teacher", False) or e_dono or e_proprietario

        # Busca o histórico permanente gravado no MySQL para este animal
        if self.paciente.get("id"):
            self.historico = carregar_historico_animal(self.paciente["id"])
            self.atualizar_card_historico()

        # Atualiza a exibição dos botões na interface
        if hasattr(self, "cadastrar_label"):
            self.cadastrar_label.show()

        if getattr(self, "is_teacher", False) and hasattr(self, "btn_cadastrar"):
            self.btn_cadastrar.show()

        if pode_alterar:
            if hasattr(self, "btn_editar_paciente"):
                self.btn_editar_paciente.show()
                self.btn_editar_paciente.setEnabled(True)
            if hasattr(self, "btn_procedimento"):
                self.btn_procedimento.show()
                self.btn_procedimento.setEnabled(True)
            if hasattr(self, "btn_medicacao"):
                self.btn_medicacao.show()
                self.btn_medicacao.setEnabled(True)
        else:
            if hasattr(self, "btn_editar_paciente"):
                self.btn_editar_paciente.hide()
            if hasattr(self, "btn_procedimento"):
                self.btn_procedimento.hide()
            if hasattr(self, "btn_medicacao"):
                self.btn_medicacao.hide()

            QMessageBox.information(
                self,
                "Modo Somente Leitura",
                f"Você está monitorando o paciente de {animal.get('nome_responsavel', 'outro usuário')}.\n\n"
                "Ações de edição, procedimento e medicação estão ocultas."
            )


    def atualizar_informacoes_paciente(self) -> None:
        cor_destaque = "#287a55" if getattr(self, "is_teacher", False) else "#08b9df"

        self.informacoes_paciente.setText(
            f"<span style='color:{cor_destaque};'><b>Nome:</b></span> {self.paciente['nome']}<br>"
            f"<span style='color:{cor_destaque};'><b>Espécie:</b></span> {self.paciente['especie']}<br>"
            f"<span style='color:{cor_destaque};'><b>Idade:</b></span> {self.paciente['idade']} anos<br>"
            f"<span style='color:{cor_destaque};'><b>Porte:</b></span> {self.paciente['porte']}<br><br>"
            f"<span style='color:{cor_destaque};'><b>Responsável:</b></span> {self.paciente['medico_procedimento']}<br>"
            f"<span style='color:{cor_destaque};'><b>Procedimento:</b></span> {self.paciente['procedimento']}<br>"
            f"<span style='color:{cor_destaque};'><b>Estado Clínico:</b></span> {self.paciente['estado_clinico']}<br>"
            f"<span style='color:{cor_destaque};'><b>Última Medicação:</b></span> {self.paciente['ultima_medicacao']} "
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

        linha_botoes = QHBoxLayout()

        self.btn_exportar_pdf = QPushButton("📄 Baixar PDF (Gráfico + Histórico)")
        self.btn_exportar_pdf.setObjectName("btn_card_animal")
        self.btn_exportar_pdf.clicked.connect(self.exportar_relatorio_pdf)
        linha_botoes.addWidget(self.btn_exportar_pdf)

        ver_mais = QPushButton("Ver Mais")
        ver_mais.setObjectName("botao_ver_mais")
        ver_mais.clicked.connect(self.ver_historico_completo)
        linha_botoes.addWidget(ver_mais, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(linha_botoes)
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
                self, "Aviso", "Selecione um animal para lançar procedimentos."
            )
            return

        dialogo = CadastrarProcedimentoDialog(self.paciente, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            # Pega o ID do usuário logado
            user_id = self.usuario.get("id") or self.usuario.get("usuario_id")

            # Salva de forma PERMANENTE no banco MySQL
            sucesso = salvar_historico_procedimento(
                animal_id=self.paciente["id"],
                realizado_por=user_id,
                procedimento=dados["procedimento"],
            )

            if sucesso:
                # Recarrega o histórico completo atualizado do banco
                self.historico = carregar_historico_animal(self.paciente["id"])
                self.paciente["procedimento"] = dados["procedimento"]
                self.paciente["medico_procedimento"] = dados["medico_procedimento"]

                self.atualizar_informacoes_paciente()
                self.atualizar_card_historico()
            else:
                QMessageBox.critical(
                    self,
                    "Erro",
                    "Falha ao salvar procedimento no banco de dados.",
                )

    def cadastrar_medicacao(self) -> None:
        if self.paciente.get("nome") == "---" or not self.paciente.get("id"):
            QMessageBox.warning(
                self, "Aviso", "Selecione um animal para lançar medicações."
            )
            return

        dialogo = CadastrarMedicacaoDialog(self.paciente, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            dados = dialogo.dados()

            user_id = self.usuario.get("id") or self.usuario.get("usuario_id")
            dose = f"{dados['quantidade']} {dados['unidade']}"

            # Salva de forma PERMANENTE no banco MySQL
            sucesso = salvar_historico_medicacao(
                animal_id=self.paciente["id"],
                administrado_por=user_id,
                medicamento=dados["medicacao"],
                dose_quantidade=dose,
            )

            if sucesso:
                # Recarrega o histórico atualizado do banco
                self.historico = carregar_historico_animal(self.paciente["id"])
                self.paciente["ultima_medicacao"] = dados["medicacao"]
                self.paciente["quantidade_medicacao"] = dose

                self.atualizar_informacoes_paciente()
                self.atualizar_card_historico()
            else:
                QMessageBox.critical(
                    self,
                    "Erro",
                    "Falha ao salvar medicação no banco de dados.",
                )
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
        # Define a cor do tema com base no perfil do usuário:
        # - Verde (#287a55) para Docente / Teacher
        # - Azul (#08b9df) para Aluno / Student
        cor_tema = "#287a55" if getattr(self, "is_teacher", False) else "#08b9df"
        cor_hover_item = "#216746" if getattr(self, "is_teacher", False) else "#078eaa"

        self.setStyleSheet(
            f"""
            /* Cabeçalho superior */
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
            #botao_menu:hover {{ color: {cor_hover_item}; }}

            /* Layout de Fundo Principal */
            #layout_fundo {{ 
                background-color: {cor_tema}; 
            }}

            /* MENU LATERAL SLIDING / DRAWER VERDE PARA DOCENTE */
            #menu_lateral, #sidebar, QFrame#menu_lateral {{
                background-color: {cor_tema};
                border-right: 2px solid rgba(255, 255, 255, 0.2);
            }}

            /* Itens e botões do Menu Lateral */
            #menu_lateral QPushButton, #sidebar QPushButton {{
                background-color: transparent;
                color: #ffffff;
                text-align: left;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 5px;
            }}
            #menu_lateral QPushButton:hover, #sidebar QPushButton:hover {{
                background-color: {cor_hover_item};
            }}

            /* Rótulos e Títulos dentro do Menu Lateral */
            #menu_lateral QLabel, #sidebar QLabel {{
                color: #ffffff;
                font-weight: bold;
            }}

            /* Cards mantidos em branco para contraste */
            #card {{
                background-color: #ffffff;
                border: none;
                border-radius: 10px;
            }}
            #card QLabel {{ 
                color: #1a1a1a; 
                font-size: 14px; 
            }}
            #card QLabel b {{ 
                color: {cor_tema}; 
            }}

            #titulo_secao {{
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }}

            #btn_card_animal {{
                background-color: {cor_tema};
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: 600;
                font-size: 12px;
            }}
            #btn_card_animal:hover {{ 
                background-color: {cor_hover_item}; 
            }}

            QTextEdit, QLineEdit {{
                background-color: #ffffff;
                color: #1a1a1a;
            }}
            """
        )