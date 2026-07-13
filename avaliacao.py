"""
avaliacao.py — Fase 5 (Avaliação): valida o pipeline em VÁRIAS camadas.

Nunca confiamos num número só. Aqui medimos:

  Camada 1 — Baseline vs verdade oficial da NASA:
      o score_risco (baseline) prevê a flag `is_potentially_hazardous_asteroid`?
      Métricas: matriz de confusão, precisão, recall, F1, acurácia e AUC.

  Camada 2 — Concordância LLM vs baseline:
      os objetos que o LLM destacou coincidem com o topo do ranking físico?
      Métrica: sobreposição (Jaccard) dos nomes.

  Camada 3 — Auditoria da REGRA DE OURO:
      todo número citado pelo LLM realmente existe nos dados? (checagem factual)

Tudo em numpy/pandas puro — sem dependências pesadas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from schema import RelatorioSemanal

LIMIAR_PADRAO = 50.0  # score_risco >= limiar => "previsto perigoso" pelo baseline


@dataclass
class MetricasBaseline:
    limiar: float
    n: int
    n_perigosos: int
    tp: int
    fp: int
    fn: int
    tn: int
    precisao: float
    recall: float
    f1: float
    acuracia: float
    auc: float


def avaliar_baseline(df: pd.DataFrame, limiar: float = LIMIAR_PADRAO) -> MetricasBaseline:
    """Camada 1: baseline (score_risco) como classificador da flag oficial da NASA."""
    y_true = df["perigoso_nasa"].astype(bool).to_numpy()
    y_pred = (df["score_risco"] >= limiar).to_numpy()

    tp = int(np.sum(y_pred & y_true))
    fp = int(np.sum(y_pred & ~y_true))
    fn = int(np.sum(~y_pred & y_true))
    tn = int(np.sum(~y_pred & ~y_true))

    precisao = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) else 0.0
    acuracia = (tp + tn) / len(df) if len(df) else 0.0

    return MetricasBaseline(
        limiar=limiar, n=len(df), n_perigosos=int(y_true.sum()),
        tp=tp, fp=fp, fn=fn, tn=tn,
        precisao=round(precisao, 3), recall=round(recall, 3),
        f1=round(f1, 3), acuracia=round(acuracia, 3),
        auc=round(_auc(df["score_risco"].to_numpy(), y_true), 3),
    )


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUC via estatística de Mann-Whitney (com ranks médios para empates)."""
    labels = labels.astype(bool)
    n_pos, n_neg = int(labels.sum()), int((~labels).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = pd.Series(scores).rank().to_numpy()  # ranks médios tratam empates
    soma_ranks_pos = ranks[labels].sum()
    return (soma_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def concordancia_llm_baseline(
    rel: RelatorioSemanal, df: pd.DataFrame, top_n: int = 3
) -> dict:
    """Camada 2: sobreposição entre destaques do LLM e o top-N do baseline (Jaccard)."""
    top_baseline = set(df.head(top_n)["nome"])
    destaques_llm = {o.nome for o in rel.objetos_destaque}
    intersec = top_baseline & destaques_llm
    uniao = top_baseline | destaques_llm
    return {
        "top_baseline": sorted(top_baseline),
        "destaques_llm": sorted(destaques_llm),
        "jaccard": round(len(intersec) / len(uniao), 3) if uniao else 0.0,
        "cobertura": round(len(intersec) / len(top_baseline), 3) if top_baseline else 0.0,
    }


@dataclass
class AuditoriaRegraDeOuro:
    ok: bool
    violacoes: list[str] = field(default_factory=list)
    numeros_conferidos: int = 0


def auditar_regra_de_ouro(
    rel: RelatorioSemanal, df: pd.DataFrame, tolerancia: float = 0.05
) -> AuditoriaRegraDeOuro:
    """
    Camada 3: confere se cada número citado nos objetos_destaque existe nos dados.

    Para cada destaque, o nome tem de existir e score/distância/diâmetro têm de
    bater (dentro de `tolerancia` relativa) com a linha real. Qualquer divergência
    é uma violação da regra de ouro.
    """
    violacoes: list[str] = []
    conferidos = 0
    indexado = df.set_index("nome")

    for o in rel.objetos_destaque:
        if o.nome not in indexado.index:
            violacoes.append(f"Objeto inexistente nos dados: '{o.nome}'.")
            continue
        linha = indexado.loc[o.nome]
        if isinstance(linha, pd.DataFrame):  # nome duplicado — pega o primeiro
            linha = linha.iloc[0]
        for campo, valor_llm in (
            ("score_risco", o.score_risco),
            ("distancia_lunar", o.distancia_lunar),
            ("diametro_m", o.diametro_m),
        ):
            conferidos += 1
            real = float(linha[campo])
            if abs(valor_llm - real) > max(tolerancia * abs(real), 0.5):
                violacoes.append(
                    f"'{o.nome}'.{campo}: LLM disse {valor_llm}, dado real é {real}."
                )

    return AuditoriaRegraDeOuro(
        ok=not violacoes, violacoes=violacoes, numeros_conferidos=conferidos
    )


def relatorio_avaliacao(df: pd.DataFrame, rel: RelatorioSemanal | None = None) -> dict:
    """Agrega as camadas num dicionário (usado pelo paper e pelos logs)."""
    saida: dict = {"baseline": avaliar_baseline(df).__dict__}
    if rel is not None:
        saida["concordancia"] = concordancia_llm_baseline(rel, df)
        saida["regra_de_ouro"] = auditar_regra_de_ouro(rel, df).__dict__
    return saida


if __name__ == "__main__":
    from score import calcular_score
    from coleta import coletar_semana

    df = calcular_score(coletar_semana())
    m = avaliar_baseline(df)
    print("=== Camada 1 — Baseline vs flag oficial da NASA ===")
    print(f"n={m.n} | perigosos={m.n_perigosos} | limiar={m.limiar}")
    print(f"Confusão: TP={m.tp} FP={m.fp} FN={m.fn} TN={m.tn}")
    print(f"Precisão={m.precisao} Recall={m.recall} F1={m.f1} Acurácia={m.acuracia} AUC={m.auc}")
