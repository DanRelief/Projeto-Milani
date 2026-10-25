import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.ia.llm.modelos_saida import (
    RelatorioGemini,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

load_dotenv(
    PROJECT_ROOT / ".env"
)


class GeminiClient:

    def __init__(self,api_key: str | None = None,modelo: str = "gemini-flash-latest",) -> None:

        chave = (
            api_key
            or os.getenv("API_KEY_GEMINI")
        )

        if not chave:
            raise ValueError(
                "API_KEY_GEMINI não configurada."
            )

        self.modelo = modelo

        self.cliente = genai.Client(
            api_key=chave
        )

    def gerar_relatorio(
        self,
        prompt: str,
    ) -> RelatorioGemini:

        resposta = (
            self.cliente.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type=(
                        "application/json"
                    ),
                    response_schema=(
                        RelatorioGemini
                    ),
                ),
            )
        )

        if not resposta.text:
            raise RuntimeError(
                "Gemini retornou resposta vazia."
            )

        return (
            RelatorioGemini
            .model_validate_json(
                resposta.text
            )
        )