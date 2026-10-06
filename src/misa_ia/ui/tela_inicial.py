from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout
)
from pathlib import Path
from PySide6.QtGui import QPixmap

class TelaInicial(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('M.I.S.A - Tela Inicial')
        self.resize(800,600)
        self.setMinimumSize(800,600)
        

        central = QWidget()
        central.setObjectName("layout_fundo")
        layout_fundo = QVBoxLayout(central)
        layout_fundo.setContentsMargins(0, 0, 0, 0)
        layout_fundo.setSpacing(0)

        # Header - Cabeçalho Inicial
        cabecalho = QWidget()
        cabecalho.setObjectName("cabecalho")
        cabecalho.setFixedHeight(75)
        layout_cabecalho = QHBoxLayout(cabecalho)
        layout_cabecalho.setContentsMargins(16, 0, 16, 0)
        layout_cabecalho.setSpacing(24)

        caminho_logo = Path(__file__).resolve().parents[3] / "logo_misa.png"

        logo = QLabel()
        imagem_logo = QPixmap(str(caminho_logo))
        logo.setPixmap(imagem_logo.scaled(240,85,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

        dados_aluno = QLabel(
            '<span style="color:#08b9df;"><b>Aluno:</b></span> Bryan<br>'
            '<span style="color:#08b9df;"><b>RA:</b></span> 1115152'
        )

        dados_professor = QLabel(
            '<span style="color:#08b9df;"><b>Professor:</b></span> Milani'
        )

        # Botão do menu lateral
        botao_menu = QPushButton("☰")
        botao_menu.setObjectName("botao_menu")

        titulo = QLabel("M.I.S.A")
        titulo.setStyleSheet("font-size: 50px; font-weight: bold; color: #08b9df;")
        layout_cabecalho.addWidget(logo)
        layout_cabecalho.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignTop)
        layout_cabecalho.addWidget(dados_aluno)
        layout_cabecalho.addStretch()
        layout_cabecalho.addWidget(dados_professor)
        layout_cabecalho.addWidget(botao_menu)
        layout_cabecalho.setAlignment(Qt.AlignmentFlag.AlignTop)

        
        layout_fundo.addWidget(cabecalho, alignment=Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet(
            """
            #cabecalho {
                background-color: white;
            }

            #cabecalho QLabel {
                font-size: 18px;
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

            #layout_fundo{
            
                background-color: #08b9df;
            }
            """
        )

        self.setCentralWidget(central)
