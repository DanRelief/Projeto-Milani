import sys
from PySide6.QtWidgets import QApplication
from .ui.tela_inicial import TelaInicial

def main() -> int:
    """Cria a aplicação e exibe a tela inicial."""
    application = QApplication(sys.argv)
    window = TelaInicial()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

