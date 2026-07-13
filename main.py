"""
main.py — orquestra o pipeline Sentinela ponta a ponta.

    coleta (NASA) → score (baseline) → avaliação → resumo (LLM) → WhatsApp

Salva os artefatos em saidas/ (regra de ouro: tudo que aparece no paper/mensagem
nasce de uma execução real, versionável).

Uso:
    python main.py                  # pipeline completo (precisa das chaves no .env)
    python main.py --simular-llm    # usa resumo determinístico (sem chave de LLM)
    python main.py --sem-envio      # não envia WhatsApp (só gera artefatos)
    python main.py --simular-llm --sem-envio   # dry-run completo, offline
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from avaliacao import relatorio_avaliacao
from coleta import coletar_semana
from resumo import gerar_resumo, gerar_resumo_simulado
from score import calcular_score

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("sentinela")

SAIDAS = Path(__file__).parent / "saidas"


def executar(simular_llm: bool = False, enviar: bool = True) -> dict:
    SAIDAS.mkdir(exist_ok=True)

    log.info("1/5 Coletando a semana na NASA NeoWs...")
    df = coletar_semana()
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

    from notifica import formatar_mensagem

    mensagem = formatar_mensagem(rel)
    (SAIDAS / "mensagem.txt").write_text(mensagem, encoding="utf-8")

    log.info("5/5 Envio pelo WhatsApp...")
    if enviar:
        from notifica import enviar_mensagem

        retorno = enviar_mensagem(mensagem)
        log.info("   enviado: %s", retorno.get("messages", retorno))
    else:
        log.info("   pulado (--sem-envio). Prévia da mensagem:\n%s", mensagem)

    log.info("Concluído. Artefatos em %s", SAIDAS)
    return {"df": df, "relatorio": rel, "avaliacao": aval, "mensagem": mensagem}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Pipeline Sentinela — radar semanal de asteroides.")
    p.add_argument("--simular-llm", action="store_true", help="resumo sem IA (offline/CI).")
    p.add_argument("--sem-envio", action="store_true", help="não envia WhatsApp.")
    args = p.parse_args()
    executar(simular_llm=args.simular_llm, enviar=not args.sem_envio)
