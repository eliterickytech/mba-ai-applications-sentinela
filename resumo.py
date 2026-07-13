"""
resumo.py — Fase 4 (Modelagem/LLM): resumo executivo com saída estruturada.

Usa a API da Anthropic (claude-haiku-4-5, temperature=0) e FORÇA o modelo a
devolver o schema `RelatorioSemanal` via tool use (structured output). O LLM
apenas ORGANIZA e COMUNICA os números que já vêm dos dados — nunca inventa
(REGRA DE OURO reforçada no system prompt e verificada depois em avaliacao.py).

Há também `gerar_resumo_simulado()`: um fallback determinístico, SEM IA, que
monta o mesmo schema a partir dos dados. Serve para rodar o pipeline em CI ou
sem chave de API — deixando claro que não é o resultado do LLM.

Uso:
    python resumo.py            # requer ANTHROPIC_API_KEY no .env
    python resumo.py --simular  # fallback sem IA
"""

from __future__ import annotations

import json
import os
import sys

import pandas as pd
from dotenv import load_dotenv

from schema import AsteroideDestaque, RelatorioSemanal

load_dotenv()

MODELO = "claude-haiku-4-5"
TOP_N_CONTEXTO = 12  # nº de linhas enviadas ao LLM (economia de tokens)

SYSTEM_PROMPT = """Você é analista de defesa planetária de um núcleo de divulgação \
científica. Sua tarefa é transformar a lista semanal de asteroides próximos da Terra \
em um resumo executivo claro, para quem decide onde focar atenção e comunicação.

REGRAS (inegociáveis):
- REGRA DE OURO: use SOMENTE números presentes nos dados fornecidos. Nunca invente, \
arredonde de forma enganosa nem estime valores ausentes.
- Escreva em português do Brasil, tom executivo e acessível ao público geral.
- 'perigoso_nasa=True' é a classificação oficial da NASA (objeto potencialmente \
perigoso). O 'score_risco' é um baseline físico interno (0-100) da própria semana.
- Se houver algum objeto com perigoso_nasa=True, o campo 'alerta' deve mencioná-lo; \
caso contrário, 'alerta' deve ser null.
- Os objetos_destaque devem sair da lista fornecida, priorizando maior score_risco \
e/ou perigoso_nasa=True."""


def _preparar_contexto(df: pd.DataFrame) -> str:
    """Monta um contexto enxuto (JSON) com o topo da semana + estatísticas reais."""
    colunas = [
        "nome", "diametro_m", "velocidade_kms", "distancia_lunar",
        "score_risco", "nivel", "perigoso_nasa", "sentry_nasa",
    ]
    topo = df[colunas].head(TOP_N_CONTEXTO)
    contexto = {
        "estatisticas_semana": {
            "total_asteroides": int(len(df)),
            "perigosos_nasa": int(df["perigoso_nasa"].sum()),
            "maior_diametro_m": float(df["diametro_m"].max()),
            "menor_distancia_lunar": float(df["distancia_lunar"].min()),
        },
        "asteroides_topo": topo.to_dict(orient="records"),
    }
    return json.dumps(contexto, ensure_ascii=False, indent=2)


def gerar_resumo(df: pd.DataFrame) -> RelatorioSemanal:
    """Chama o LLM com structured output e devolve um RelatorioSemanal validado."""
    import anthropic  # import tardio: só é preciso no caminho com IA

    if df.empty:
        raise ValueError("DataFrame vazio — nada a resumir.")

    cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    # A "ferramenta" carrega o JSON Schema do Pydantic: o modelo é forçado a preenchê-la.
    ferramenta = {
        "name": "registrar_relatorio_semanal",
        "description": "Registra o resumo executivo estruturado da semana de asteroides.",
        "input_schema": RelatorioSemanal.model_json_schema(),
    }

    resposta = cliente.messages.create(
        model=MODELO,
        max_tokens=1500,
        temperature=0,
        system=SYSTEM_PROMPT,
        tools=[ferramenta],
        tool_choice={"type": "tool", "name": "registrar_relatorio_semanal"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Dados reais da semana (NASA NeoWs). Gere o relatório executivo:\n\n"
                    + _preparar_contexto(df)
                ),
            }
        ],
    )

    for bloco in resposta.content:
        if bloco.type == "tool_use":
            return RelatorioSemanal.model_validate(bloco.input)
    raise RuntimeError("O modelo não retornou a ferramenta estruturada esperada.")


def gerar_resumo_simulado(df: pd.DataFrame) -> RelatorioSemanal:
    """
    Fallback SEM IA: monta o schema direto dos dados (determinístico).
    Usado em CI/sem chave. Todos os números vêm dos dados (regra de ouro).
    """
    if df.empty:
        raise ValueError("DataFrame vazio — nada a resumir.")

    total = int(len(df))
    n_perigosos = int(df["perigoso_nasa"].sum())
    topo = df.head(3)

    destaques = [
        AsteroideDestaque(
            nome=r["nome"],
            motivo=(
                f"{'Classificado como perigoso pela NASA; ' if r['perigoso_nasa'] else ''}"
                f"passa a {r['distancia_lunar']:.0f} distâncias lunares."
            ),
            score_risco=float(r["score_risco"]),
            distancia_lunar=float(r["distancia_lunar"]),
            diametro_m=float(r["diametro_m"]),
        )
        for _, r in topo.iterrows()
    ]

    nivel = "Elevada" if n_perigosos >= 3 else "Atenção" if n_perigosos >= 1 else "Tranquila"
    mais_perto = df.loc[df["distancia_lunar"].idxmin()]

    return RelatorioSemanal(
        titulo=f"Radar da semana: {total} asteroides monitorados",
        nivel_semana=nivel,
        resumo_executivo=(
            f"A NASA registrou {total} aproximações nesta semana, sendo {n_perigosos} "
            f"classificadas como potencialmente perigosas. O objeto mais próximo passou "
            f"a {mais_perto['distancia_lunar']:.0f} distâncias lunares."
        ),
        bullets=[
            f"{total} asteroides monitorados na semana.",
            f"{n_perigosos} com flag oficial de risco da NASA.",
            f"Maior objeto: {df['diametro_m'].max():.0f} m de diâmetro.",
            f"Passagem mais próxima: {df['distancia_lunar'].min():.1f} distâncias lunares.",
        ],
        objetos_destaque=destaques,
        numero_destaque=f"{total} asteroides monitorados",
        alerta=(
            f"{n_perigosos} objeto(s) marcados como potencialmente perigosos pela NASA."
            if n_perigosos
            else None
        ),
    )


if __name__ == "__main__":
    from score import calcular_score
    from coleta import coletar_semana

    df = calcular_score(coletar_semana())
    simular = "--simular" in sys.argv
    rel = gerar_resumo_simulado(df) if simular else gerar_resumo(df)
    print(("[SIMULADO] " if simular else "[LLM] ") + rel.titulo)
    print(json.dumps(rel.model_dump(), ensure_ascii=False, indent=2))
