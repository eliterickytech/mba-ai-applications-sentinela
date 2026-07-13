"""
schema.py — contratos de saída estruturada (Pydantic).

Estes schemas são o coração da "saída estruturada" exigida pela disciplina:
o LLM é OBRIGADO a devolver exatamente estes campos. Schema fixo = resultado
comparável, validável e pronto para virar mensagem de WhatsApp.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AsteroideDestaque(BaseModel):
    """Um objeto que o relatório coloca em evidência na semana."""

    nome: str = Field(description="Designação do asteroide, exatamente como nos dados.")
    motivo: str = Field(
        description="Por que merece atenção, em 1 frase de negócio (sem jargão)."
    )
    score_risco: float = Field(
        description="Score de risco 0-100 do baseline, copiado dos dados."
    )
    distancia_lunar: float = Field(
        description="Distância de passagem em distâncias lunares, copiada dos dados."
    )
    diametro_m: float = Field(description="Diâmetro médio em metros, copiado dos dados.")


class RelatorioSemanal(BaseModel):
    """Resumo executivo da semana de asteroides — a saída do LLM."""

    titulo: str = Field(description="Título curto e informativo da semana.")
    nivel_semana: str = Field(
        description="Classificação geral da semana: 'Tranquila', 'Atenção' ou 'Elevada'."
    )
    resumo_executivo: str = Field(
        description="2-3 frases em linguagem executiva resumindo a semana."
    )
    bullets: list[str] = Field(
        description="3 a 5 pontos objetivos, cada um citando números vindos dos dados.",
    )
    objetos_destaque: list[AsteroideDestaque] = Field(
        description="1 a 3 asteroides de maior atenção na semana (ordem de risco).",
    )
    numero_destaque: str = Field(
        description="O número mais marcante da semana (ex.: '32 asteroides monitorados')."
    )
    alerta: Optional[str] = Field(
        default=None,
        description="Alerta objetivo se houver objeto perigoso; caso contrário, null.",
    )
