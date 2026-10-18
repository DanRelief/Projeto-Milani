from pathlib import Path
from uuid import uuid4

from src.infrastructure.database import salvar_observacao_docente

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

        self.is_teacher = usuario.get("role") in ["Docente", "teacher"]
        self.sessao_ativa_id = None # Armazena o UUID da sessão em sessoes_monitoramento

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

    def _carregar_animal_para_monitoramento(self, animal: dict, e_proprietario: bool) -> None:
        # 1. Atualiza o dicionário local do paciente com os dados do MySQL
        self.paciente["id"] = animal.get("id")
        self.paciente["nome"] = animal["nome"]
        self.paciente["especie"] = animal["especie"]
        self.paciente["idade"] = animal["idade"]
        self.paciente["porte"] = animal["porte"].capitalize()
        self.paciente["procedimento"] = animal["procedimento"]
        self.paciente["estado_clinico"] = animal["estado_clinico"].capitalize()
        self.paciente["ultima_medicacao"] = animal.get("ultima_medicacao") or "Nenhuma"
        self.paciente["quantidade_medicacao"] = animal.get("quantidade") or "N/A"
        self.paciente["medico_procedimento"] = animal.get("nome_responsavel", "Desconhecido")
        self.paciente["observacao_docente"] = animal.get("observacao_docente") or ""

        responsavel_db = animal.get("responsavel_aplicacao") or animal.get("responsavel_id")
        self.paciente["responsavel_id"] = responsavel_db

        self.atualizar_informacoes_paciente()

        # Atualiza a caixa de observação se ela existir na interface
        if hasattr(self, "campo_observacao"):
            self.campo_observacao.setText(self.paciente["observacao_docente"])

        # 2. Recupera o ID do usuário logado (com suporte a ambas as chaves)
        user_id_logado = self.usuario.get("id") or self.usuario.get("usuario_id")

        # 3. Compara os IDs convertendo para int de forma segura
        try:
            e_dono = (int(user_id_logado) == int(responsavel_db)) if (user_id_logado and responsavel_db) else False
        except (ValueError, TypeError):
            e_dono = False

        # O aluno pode alterar se for o dono do animal. O docente pode alterar qualquer um.
        pode_alterar = self.is_teacher or e_dono or e_proprietario

        # Sempre exibe o rótulo da seção de ações ao carregar um animal
        if hasattr(self, "cadastrar_label"):
            self.cadastrar_label.show()

        # O botão Cadastrar Animal continua restrito ao Docente
        if self.is_teacher:
            self.btn_cadastrar.show()

        if pode_alterar:
            # Reexibe os botões na tela
            self.btn_editar_paciente.show()
            self.btn_procedimento.show()
            self.btn_medicacao.show()

            self.btn_editar_paciente.setEnabled(True)
            self.btn_procedimento.setEnabled(True)
            self.btn_medicacao.setEnabled(True)
        else:
            self.btn_editar_paciente.hide()
            self.btn_procedimento.hide()
            self.btn_medicacao.hide()

            QMessageBox.information(
                self,
                "Modo Somente Leitura",
                f"Você está monitorando o paciente de {animal.get('nome_responsavel', 'outro aluno')}.\n\n"
                "Ações de edição, procedimento e medicação não estão disponíveis."
            )

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

        # 1. Recupera o papel do usuário logado (com suporte a 'teacher' do MySQL)
        user_role = str(self.usuario.get("role", "")).strip().lower()
        self.is_teacher = user_role in ["teacher", "docente", "professor", "admin"]

        # Informações do Paciente
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

        # 2. Caixa de Observação do Docente
        label_obs = QLabel("<b>Observações do Docente:</b>")
        label_obs.setStyleSheet("color: #08b9df; font-size: 13px; margin-top: 4px;")
        layout.addWidget(label_obs)

        self.campo_observacao = QTextEdit()
        self.campo_observacao.setPlaceholderText("Escreva observações e orientações para os alunos...")
        self.campo_observacao.setMaximumHeight(50)
        self.campo_observacao.setStyleSheet("""
            QTextEdit {
                border: 1px solid #c7d0d9;
                border-radius: 5px;
                padding: 4px;
                font-size: 12px;
                background-color: #ffffff;
                color: #1a1a1a;
            }
        """)

        if not self.is_teacher:
            self.campo_observacao.setReadOnly(True)
            self.campo_observacao.setPlaceholderText("Nenhuma observação cadastrada pelo docente.")

        layout.addWidget(self.campo_observacao)

        if self.is_teacher:
            self.btn_salvar_obs = QPushButton("Salvar Observação")
            self.btn_salvar_obs.setObjectName("btn_card_animal")
            self.btn_salvar_obs.setFixedHeight(26)
            self.btn_salvar_obs.clicked.connect(self._salvar_observacao_docente)
            layout.addWidget(self.btn_salvar_obs, alignment=Qt.AlignmentFlag.AlignRight)

        # 3. Seção AÇÕES DO ANIMAL
        self.cadastrar_label = QLabel("AÇÕES DO ANIMAL")
        self.cadastrar_label.setObjectName("titulo_cadastrar")
        self.cadastrar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cadastrar_label)

        # Linha com os Botões de Gestão
        linha_botoes_animais = QHBoxLayout()
        linha_botoes_animais.addStretch()

        self.btn_cadastrar = QPushButton("Cadastrar Animal")
        self.btn_cadastrar.setObjectName("btn_card_animal")
        self.btn_cadastrar.clicked.connect(self._abrir_cadastro_animal)
        
        # REGRA DE EXIBIÇÃO: Se for docente, exibe o botão imediatamente
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

        # Linha com os Botões Clínicos (Iniciam ocultos)
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
        self.grafico.setTitle("Monitoramento em Tempo Real (IA Teste)")
        self.grafico.setAnimationOptions(QChart.AnimationOption.NoAnimation)

        self.grafico_view = QChartView(self.grafico)
        self.grafico_view.setFrameShape(QFrame.Shape.NoFrame)
        self.grafico_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.grafico_view, 1)

        # 3 Séries para Teste
        self.oxigenio_serie = QSplineSeries()
        self.oxigenio_serie.setName("Oxigênio (%)")

        self.pressao_serie = QSplineSeries()
        self.pressao_serie.setName("Pressão Arterial (mmHg)")

        self.temperatura_serie = QSplineSeries()
        self.temperatura_serie.setName("Temperatura (°C)")

        self.grafico.addSeries(self.oxigenio_serie)
        self.grafico.addSeries(self.pressao_serie)
        self.grafico.addSeries(self.temperatura_serie)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Amostras / Tempo")
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setRange(0, 30)

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 150)
        self.axis_y.setTitleText("Valor")

        self.grafico.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.grafico.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        for series in (self.oxigenio_serie, self.pressao_serie, self.temperatura_serie):
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        return card

    def update_chart(self, medicao) -> None:
        index = self.oxigenio_serie.count()

        # Adiciona os valores do objeto Measurement
        self.oxigenio_serie.append(float(index), float(getattr(medicao, "oxigenio", 0.0)))
        self.pressao_serie.append(float(index), float(getattr(medicao, "pressao_arterial", 0.0)))
        self.temperatura_serie.append(float(index), float(getattr(medicao, "temperatura", 0.0)))

        JANELA_MAXIMA = 30
        if index >= JANELA_MAXIMA:
            self.axis_x.setRange(index - JANELA_MAXIMA + 1, index)
        else:
            self.axis_x.setRange(0, JANELA_MAXIMA)

        BUFFER_MAXIMO = 150
        if self.oxigenio_serie.count() > BUFFER_MAXIMO:
            self.oxigenio_serie.remove(0)
            self.pressao_serie.remove(0)
            self.temperatura_serie.remove(0)

    def _abrir_cadastro_animal(self) -> None:
        dlg = DialogCadastrarAnimal(self.usuario, self)
        dlg.exec()

    def _abrir_selecao_animal(self) -> None:
        dlg = DialogSelecionarAnimal(self.usuario, self)
        dlg.animal_selecionado.connect(self._carregar_animal_para_monitoramento)
        dlg.exec()


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
