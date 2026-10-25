import json
from dataclasses import asdict
from datetime import datetime

from src.ia.llm.modelos_contexto import (
    ContextoRelatorio,
)


def _converter_json(valor):
    """
    Converte objetos que o json.dumps
    não serializa nativamente.
    """

    if isinstance(valor, datetime):
        return valor.isoformat()

    if hasattr(valor, "value"):
        return valor.value

    raise TypeError(
        f"Tipo não serializável: {type(valor)}"
    )


def contexto_para_json(
    contexto: ContextoRelatorio,
) -> str:

    dados = asdict(
        contexto
    )

    return json.dumps(
        dados,
        ensure_ascii=False,
        indent=2,
        default=_converter_json,
    )


def construir_prompt_relatorio(
    contexto: ContextoRelatorio,
) -> str:

    contexto_json = contexto_para_json(
        contexto
    )

    prompt = f"""
Você é um assistente de apoio à análise de uma
sessão de monitoramento veterinário.

Sua tarefa é gerar um relatório descritivo e
estruturado EXCLUSIVAMENTE a partir dos dados
fornecidos pelo sistema M.I.S.A.

REGRAS OBRIGATÓRIAS

1. Não invente informações.

2. Não faça diagnóstico clínico.

3. Não prescreva medicamentos, tratamentos,
procedimentos ou intervenções.

4. Não estabeleça causalidade clínica sem que
ela esteja explicitamente registrada nos dados.

Exemplo permitido:
"A redução da SpO₂ foi registrada após a
administração do medicamento X."

Exemplo não permitido:
"O medicamento X causou a redução da SpO₂."

5. Diferencie claramente:
- dados medidos;
- resultados dos algoritmos;
- alertas gerados pelo sistema;
- procedimentos;
- medicações;
- observações humanas.

6. Um alerta do M.I.S.A representa uma alteração
detectada pelos algoritmos do sistema e NÃO um
diagnóstico veterinário.

7. Considere a ordem cronológica dos eventos.

8. Se uma informação necessária não estiver
presente, registre-a em "informacoes_ausentes".

9. Não complete informações ausentes usando
conhecimento externo.

10. Utilize os valores, unidades, horários,
nomes e eventos conforme fornecidos.

11. Ao descrever relações entre medicações,
procedimentos e alterações dos sinais, utilize
linguagem temporal e não causal.

12. Considere no resumo dos sinais:
- valor inicial;
- valor final;
- mínimo;
- máximo;
- média;
- mediana;
- quantidade de medições;
- alertas registrados.

13. Utilize as análises atuais do sistema como
evidência complementar, quando disponíveis.

14. Não trate Z-score robusto, EWMA ou qualquer
outro indicador estatístico como diagnóstico
clínico.

15. O relatório deve deixar claro que se trata
de apoio à interpretação e que a avaliação final
cabe ao profissional veterinário responsável.

DADOS DA SESSÃO EM FORMATO JSON:

{contexto_json}

Produza o relatório exclusivamente com base
nos dados acima.
"""

    return prompt.strip()