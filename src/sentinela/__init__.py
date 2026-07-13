"""Sentinela — radar semanal de risco de asteroides (CRISP-DM + LLM).

Arquitetura em camadas (dependência aponta para dentro):
    aplicacao ─▶ infra ─▶ dominio
    aplicacao ───────────▶ dominio

- dominio/  : regras de negócio puras (entidades, score, avaliação). Sem I/O.
- infra/    : adaptadores externos (NASA, OpenAI, WhatsApp).
- aplicacao/: casos de uso que orquestram domínio + infra.
"""

__version__ = "1.0.0"
