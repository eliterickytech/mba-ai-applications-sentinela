"""
CLI do Sentinela — interface de linha de comando (adaptador de entrada).

    python -m sentinela                       # pipeline completo (precisa das chaves)
    python -m sentinela --simular-llm         # resumo determinístico (sem chave de LLM)
    python -m sentinela --sem-envio           # não envia WhatsApp (só gera artefatos)
    python -m sentinela --simular-llm --sem-envio   # dry-run offline
"""

from __future__ import annotations

import argparse
import logging

from .aplicacao.pipeline import executar


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    p = argparse.ArgumentParser(
        prog="sentinela", description="Pipeline Sentinela — radar semanal de asteroides."
    )
    p.add_argument("--simular-llm", action="store_true", help="resumo sem IA (offline/CI).")
    p.add_argument("--sem-envio", action="store_true", help="não envia WhatsApp.")
    args = p.parse_args()
    executar(simular_llm=args.simular_llm, enviar=not args.sem_envio)


if __name__ == "__main__":
    main()
