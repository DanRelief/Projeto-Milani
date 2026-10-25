from src.ia.llm.construtor_contexto import (
    ConstrutorContextoRelatorio,
)

from src.ia.llm.construtor_prompt import (
    construir_prompt_relatorio,
)

from src.ia.llm.gemini_client import (
    GeminiClient,
)

from src.ia.llm.modelos_saida import (
    RelatorioGemini,
)


class ErroGeracaoRelatorio(Exception):
    """
    Erro ocorrido durante a geração
    do relatório por IA.
    """


class ServicoRelatorio:

    def __init__(
        self,
        construtor_contexto=None,
        cliente_gemini=None,
    ) -> None:

        self.construtor_contexto = (
            construtor_contexto
            if construtor_contexto is not None
            else ConstrutorContextoRelatorio()
        )

        self.cliente_gemini = (
            cliente_gemini
            if cliente_gemini is not None
            else GeminiClient()
        )

    def gerar(
        self,
        id_sessao: str,
        analises_atuais: dict | None = None,
    ) -> RelatorioGemini:

        if not id_sessao:
            raise ValueError(
                "O id da sessão é obrigatório."
            )

        try:
            contexto = (
                self.construtor_contexto.construir(
                    id_sessao=id_sessao,
                    analises_atuais=analises_atuais,
                )
            )

            prompt = (
                construir_prompt_relatorio(
                    contexto
                )
            )

            return (
                self.cliente_gemini
                .gerar_relatorio(
                    prompt
                )
            )

        except ValueError:
            raise

        except Exception as erro:
            raise ErroGeracaoRelatorio(
                "Não foi possível gerar "
                "o relatório por IA."
            ) from erro