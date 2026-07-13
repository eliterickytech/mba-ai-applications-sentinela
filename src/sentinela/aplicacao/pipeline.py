"""
aplicacao/pipeline.py — orquestra o caso de uso Sentinela, ponta a ponta.

    coleta (NASA) → score (baseline) → avaliação → resumo (LLM) → WhatsApp

Camada de aplicação: depende do domínio e da infra, mas recebe os adaptadores por
INJEÇÃO (coletor/notificador), então o caso de uso não fica preso a implementações
concretas — facilita teste e troca de fornecedor (DIP).

Salva os artefatos em saidas/ (regra de ouro: tudo que aparece no paper/mensagem
nasce de uma execução real, versionável).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

import pandas as pd

from ..dominio.avaliacao import relatorio_avaliacao
from ..dominio.risco import calcular_score
from ..infra.llm import gerar_resumo, gerar_resumo_simulado
from ..infra.nasa import coletar_semana
from ..infra.whatsapp import enviar_mensagem, formatar_mensagem

log = logging.getLogger("sentinela")

# Raiz do projeto: .../src/sentinela/aplicacao/pipeline.py -> parents[3]
RAIZ = Path(__file__).resolve().parents[3]
SAIDAS = RAIZ / "saidas"


def executar(
    simular_llm: bool = False,
    enviar: bool = True,
    *,
    coletor: Callable[[], pd.DataFrame] = coletar_semana,
    notificador: Callable[[str], dict] = enviar_mensagem,
) -> dict:
    """
    Roda o pipeline completo. `coletor` e `notificador` são injetáveis (DIP):
    por padrão usam a NASA e o WhatsApp, mas podem ser trocados (ex.: em testes).
    """
    SAIDAS.mkdir(exist_ok=True)

    log.info("1/5 Coletando a semana na NASA NeoWs...")
    df = coletor()
    if df.empty:
        log.warning("Nenhuma aproximação nesta semana — nada a enviar.")
        return {}
    log.info("   %d asteroides | %d perigosos (NASA).", len(df), int(df["perigoso_nasa"].sum()))

    log.info("2/5 Calculando o baseline de risco físico...")
    df = calcular_score(df)

    # Snapshot dos dados reais (o paper lê isto para render reprodutível).
    csv_path = SAIDAS / "amostra_semana.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    log.info("   snapshot salvo em %s", csv_path.name)

    log.info("3/5 Gerando o resumo (%s)...", "SIMULADO" if simular_llm else "LLM OpenAI GPT")
    rel = gerar_resumo_simulado(df) if simular_llm else gerar_resumo(df)

    log.info("4/5 Avaliando (baseline x NASA, concordância, regra de ouro)...")
    aval = relatorio_avaliacao(df, rel)
    m = aval["baseline"]
    log.info("   F1=%s AUC=%s | regra de ouro ok=%s",
             m["f1"], m["auc"], aval["regra_de_ouro"]["ok"])
    if not aval["regra_de_ouro"]["ok"]:
        for v in aval["regra_de_ouro"]["violacoes"]:
            log.error("   VIOLAÇÃO regra de ouro: %s", v)

    # Persiste os artefatos.
    (SAIDAS / "relatorio.json").write_text(
        json.dumps(rel.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SAIDAS / "avaliacao.json").write_text(
        json.dumps(aval, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    mensagem = formatar_mensagem(rel)
    (SAIDAS / "mensagem.txt").write_text(mensagem, encoding="utf-8")

    log.info("5/5 Envio pelo WhatsApp...")
    if enviar:
        retorno = notificador(mensagem)
        log.info("   enviado: %s", retorno.get("messages", retorno))
    else:
        log.info("   pulado (--sem-envio). Prévia da mensagem:\n%s", mensagem)

    log.info("Concluído. Artefatos em %s", SAIDAS)
    return {"df": df, "relatorio": rel, "avaliacao": aval, "mensagem": mensagem}
