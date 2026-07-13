"""
Testes do pipeline Sentinela. Rode com:  python -m pytest -q

Cobrem as partes determinísticas e sem rede: parsing da NASA, score,
métricas de avaliação e a auditoria da regra de ouro (inclusive detecção
de número inventado).
"""

from __future__ import annotations

import pandas as pd

from sentinela.dominio.avaliacao import auditar_regra_de_ouro, avaliar_baseline
from sentinela.dominio.modelos import AsteroideDestaque, RelatorioSemanal
from sentinela.dominio.risco import calcular_score
from sentinela.infra.nasa import _achatar_objeto


# --- Fixture: um objeto no formato cru da NeoWs ---
OBJ_NASA = {
    "name": "(2013 AS27)",
    "nasa_jpl_url": "http://exemplo",
    "absolute_magnitude_h": 20.0,
    "is_potentially_hazardous_asteroid": True,
    "is_sentry_object": False,
    "estimated_diameter": {"meters": {
        "estimated_diameter_min": 100.0, "estimated_diameter_max": 300.0}},
    "close_approach_data": [{
        "close_approach_date_full": "2026-Jul-06 12:00",
        "relative_velocity": {"kilometers_per_second": "17.9"},
        "miss_distance": {"lunar": "33.0", "kilometers": "12680000.0"},
    }],
}


def test_achatar_objeto_extrai_campos():
    linha = _achatar_objeto(OBJ_NASA)
    assert linha["nome"] == "2013 AS27"
    assert linha["diametro_m"] == 200.0          # média de 100 e 300
    assert linha["velocidade_kms"] == 17.9
    assert linha["distancia_lunar"] == 33.0
    assert linha["perigoso_nasa"] is True


def test_achatar_objeto_sem_aproximacao_retorna_none():
    obj = dict(OBJ_NASA, close_approach_data=[])
    assert _achatar_objeto(obj) is None


def _df_exemplo() -> pd.DataFrame:
    # Dois grandes/próximos (perigosos) e dois pequenos/distantes (não).
    dados = [
        {"nome": "A", "diametro_m": 500, "velocidade_kms": 20, "distancia_lunar": 10,
         "magnitude_h": 19, "perigoso_nasa": True, "sentry_nasa": False},
        {"nome": "B", "diametro_m": 400, "velocidade_kms": 18, "distancia_lunar": 15,
         "magnitude_h": 19, "perigoso_nasa": True, "sentry_nasa": False},
        {"nome": "C", "diametro_m": 20, "velocidade_kms": 6, "distancia_lunar": 120,
         "magnitude_h": 25, "perigoso_nasa": False, "sentry_nasa": False},
        {"nome": "D", "diametro_m": 15, "velocidade_kms": 5, "distancia_lunar": 150,
         "magnitude_h": 26, "perigoso_nasa": False, "sentry_nasa": False},
    ]
    return pd.DataFrame(dados)


def test_score_monotonico_e_ordenado():
    df = calcular_score(_df_exemplo())
    # Score entre 0 e 100 e DataFrame ordenado por risco decrescente.
    assert df["score_risco"].between(0, 100).all()
    assert df["score_risco"].is_monotonic_decreasing
    # Os perigosos (grandes/próximos) devem pontuar acima dos não-perigosos.
    assert df[df["perigoso_nasa"]]["score_risco"].min() > \
        df[~df["perigoso_nasa"]]["score_risco"].max()


def test_avaliacao_separa_classes_perfeitamente():
    df = calcular_score(_df_exemplo())
    m = avaliar_baseline(df, limiar=50)
    assert m.recall == 1.0
    assert m.auc == 1.0          # separação perfeita neste exemplo sintético


def test_regra_de_ouro_detecta_numero_inventado():
    df = calcular_score(_df_exemplo())
    real = df.iloc[0]
    rel = RelatorioSemanal(
        titulo="t", nivel_semana="Elevada", resumo_executivo="r",
        bullets=["a", "b", "c"], numero_destaque="x",
        objetos_destaque=[AsteroideDestaque(
            nome=real["nome"], motivo="m",
            score_risco=real["score_risco"],
            distancia_lunar=999.0,        # <- número INVENTADO (real é ~10)
            diametro_m=real["diametro_m"])],
    )
    audit = auditar_regra_de_ouro(rel, df)
    assert audit.ok is False
    assert any("distancia_lunar" in v for v in audit.violacoes)


def test_regra_de_ouro_aprova_numeros_corretos():
    df = calcular_score(_df_exemplo())
    real = df.iloc[0]
    rel = RelatorioSemanal(
        titulo="t", nivel_semana="Elevada", resumo_executivo="r",
        bullets=["a", "b", "c"], numero_destaque="x",
        objetos_destaque=[AsteroideDestaque(
            nome=real["nome"], motivo="m",
            score_risco=real["score_risco"],
            distancia_lunar=real["distancia_lunar"],
            diametro_m=real["diametro_m"])],
    )
    assert auditar_regra_de_ouro(rel, df).ok is True


def test_pipeline_com_dependencias_injetadas(tmp_path, monkeypatch):
    """O caso de uso roda ponta a ponta com adaptadores falsos (sem rede/LLM/WhatsApp)."""
    from sentinela.aplicacao import pipeline

    monkeypatch.setattr(pipeline, "SAIDAS", tmp_path)   # artefatos em pasta temporária
    enviados: list[str] = []

    resultado = pipeline.executar(
        simular_llm=True,                                # resumo determinístico, sem IA
        enviar=True,
        coletor=lambda: _df_exemplo(),                   # "NASA" falsa
        notificador=lambda msg: enviados.append(msg) or {"messages": [{"id": "fake"}]},
    )

    assert resultado["relatorio"].titulo
    assert len(enviados) == 1                            # o notificador injetado foi chamado
    assert (tmp_path / "relatorio.json").exists()        # artefatos persistidos
    assert (tmp_path / "amostra_semana.csv").exists()
