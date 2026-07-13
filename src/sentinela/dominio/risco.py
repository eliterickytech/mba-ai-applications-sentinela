"""
dominio/risco.py — Fase 4 (Modelagem/baseline): score de risco físico dos asteroides.

Este é o BASELINE do projeto — uma heurística transparente, sem IA, contra a qual
o resultado do LLM e a flag oficial da NASA serão comparados na Avaliação (Fase 5).

Ideia física (proxies, não valores absolutos):
  - Massa é proporcional ao volume, ou seja, ao diâmetro ao cubo (densidade ~ const).
  - Energia cinética é proporcional a massa x velocidade^2 -> diâmetro^3 x velocidade^2.
  - Quanto mais perto passa, mais relevante -> dividimos pela distância ao quadrado.

O risco bruto varia por muitas ordens de grandeza, então trabalhamos em escala log
e normalizamos para 0-100 DENTRO da semana (é um ranking relativo àquela semana).

Camada de domínio: recebe e devolve DataFrames; não faz I/O externo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Limiares do score normalizado (0-100) para rotular o nível de atenção.
LIMIARES_NIVEL = [(75, "Crítico"), (50, "Alto"), (25, "Médio"), (0, "Baixo")]


def _rotular(score: float) -> str:
    for limite, rotulo in LIMIARES_NIVEL:
        if score >= limite:
            return rotulo
    return "Baixo"


def calcular_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona as colunas `risco_bruto`, `score_risco` (0-100) e `nivel` ao DataFrame.

    Não altera o df original (trabalha numa cópia).
    """
    if df.empty:
        return df.assign(risco_bruto=[], score_risco=[], nivel=[])

    df = df.copy()

    # Energia cinética (proxy) ponderada pela proximidade.
    energia_proxy = df["diametro_m"] ** 3 * df["velocidade_kms"] ** 2
    df["risco_bruto"] = energia_proxy / (df["distancia_lunar"] ** 2)

    # Escala log (o risco bruto abrange muitas ordens de grandeza).
    risco_log = np.log10(df["risco_bruto"].clip(lower=1e-9))

    # Normalização min-max para 0-100 dentro da semana.
    lo, hi = risco_log.min(), risco_log.max()
    if hi > lo:
        df["score_risco"] = ((risco_log - lo) / (hi - lo) * 100).round(1)
    else:
        df["score_risco"] = 50.0  # semana com um único objeto ou todos iguais

    df["nivel"] = df["score_risco"].apply(_rotular)
    return df.sort_values("score_risco", ascending=False).reset_index(drop=True)
