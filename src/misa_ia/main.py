import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from .ui.tela_inicial import TelaInicial
from .ui.tela_login import TelaLogin
from .ui.estilos import ESTILO_GLOBAL


def _load_local_env() -> None:
    """Carrega variáveis simples do .env local sem exigir uma dependência extra."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def main() -> int:
    """Inicia o fluxo de login e abre a tela inicial após a autenticação."""
    _load_local_env()
    application = QApplication(sys.argv)
    application.setStyleSheet(ESTILO_GLOBAL)
    login = TelaLogin()
    home_window = None

    def open_home(usuario: dict[str, str]) -> None:
        nonlocal home_window
        home_window = TelaInicial(usuario)
        login.hide()
        home_window.show()

    login.authenticated.connect(open_home)

    if os.getenv("MISA_AUTO_LOGIN", "false").lower() == "true":
        role = os.getenv("MISA_TEST_ROLE", "student")
        index = login.role_combo.findData(role)
        if index >= 0:
            login.role_combo.setCurrentIndex(index)
        identifier = os.getenv("MISA_TEST_IDENTIFIER", "")
        password = os.getenv("MISA_TEST_PASSWORD", "")
        if not login.authenticate(role, identifier, password):
            login.show()
    else:
        login.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
