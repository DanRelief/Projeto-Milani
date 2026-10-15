import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.ui.estilos import ESTILO_GLOBAL
from src.ui.tela_inicial import TelaInicial
from src.ui.tela_login import TelaLogin


def main() -> int:
    application = QApplication(sys.argv)
    application.setStyleSheet(ESTILO_GLOBAL)

    login = TelaLogin()
    home_window = None
    primeiro_acesso_window = None

    def open_home(session: dict) -> None:
        nonlocal home_window
        home_window = TelaInicial(session)
        login.hide()
        home_window.show() # Garante a exibição da TelaInicial

        # Se for o primeiro acesso do usuário, abre a tela de cadastro primeiro
        if session.get("primeiro_acesso"):
            #primeiro_acesso_window = TelaPrimeiroAcesso(session)

            def on_cadastro_completed(final_session: dict):
                nonlocal home_window
                home_window = TelaInicial(final_session)
                primeiro_acesso_window.close()
                home_window.show()

            primeiro_acesso_window.completed.connect(on_cadastro_completed)
            login.hide()
            primeiro_acesso_window.show()
        else:
            # Acesso padrão
            home_window = TelaInicial(session)
            login.hide()
            home_window.show()
    def open_home(usuario: dict[str, str]) -> None:
        nonlocal home_window
        home_window = TelaInicial(usuario)
        home_window.logout_requested.connect(return_to_login)
        login.hide()
        home_window.show()

    def return_to_login() -> None:
        nonlocal home_window
        if home_window is not None:
            home_window.close()
            home_window = None
        login.show()
        login.raise_()
        login.activateWindow()

    login.authenticated.connect(open_home)
    login.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())