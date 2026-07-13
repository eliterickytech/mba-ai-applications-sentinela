"""
infra/nasa.py — Fase 3 (Preparação): coleta as aproximações de asteroides da semana.

Adaptador da NASA NeoWs (Near Earth Object Web Service): busca todos os objetos que
passam perto da Terra nos últimos 7 dias e devolve um DataFrame limpo e pequeno — só
as colunas que interessam ao score de risco e ao resumo.

REGRA DE OURO: todo número deste projeto nasce aqui, dos dados reais da NASA.

Uso:
    python -m sentinela.infra.nasa      # imprime um resumo da semana atual
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# A API aceita janelas de no máximo 7 dias por chamada — exatamente uma semana.
API_URL = "https://api.nasa.gov/neo/rest/v1/feed"
JANELA_DIAS = 7


def _sessao_com_retry() -> requests.Session:
    """Sessão HTTP com retry e backoff exponencial (resiliente a 429/5xx)."""
    sessao = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,  # espera 1s, 2s, 4s, 8s... entre tentativas
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    sessao.mount("https://", HTTPAdapter(max_retries=retry))
    return sessao


def _achatar_objeto(obj: dict) -> dict | None:
    """Extrai de um objeto da NeoWs só os campos que usamos, já no formato final."""
    aproximacoes = obj.get("close_approach_data") or []
    if not aproximacoes:
        return None  # sem dados de aproximação no período — descarta
    ca = aproximacoes[0]

    diam = obj["estimated_diameter"]["meters"]
    diametro_medio = (
        diam["estimated_diameter_min"] + diam["estimated_diameter_max"]
    ) / 2

    return {
        "nome": obj["name"].strip("() "),
        "data_aproximacao": ca["close_approach_date_full"],
        "diametro_m": round(diametro_medio, 1),
        "velocidade_kms": round(
            float(ca["relative_velocity"]["kilometers_per_second"]), 2
        ),
        "distancia_lunar": round(float(ca["miss_distance"]["lunar"]), 1),
        "distancia_km": round(float(ca["miss_distance"]["kilometers"]), 0),
        "magnitude_h": obj["absolute_magnitude_h"],
        "perigoso_nasa": obj["is_potentially_hazardous_asteroid"],
        "sentry_nasa": obj["is_sentry_object"],
        "url_jpl": obj["nasa_jpl_url"],
    }


def coletar_semana(fim: date | None = None) -> pd.DataFrame:
    """
    Coleta as aproximações dos últimos 7 dias (até `fim`, padrão = hoje).

    Retorna um DataFrame ordenado pela menor distância (mais próximo primeiro).
    Levanta erro claro se a rede/API falhar após os retries.
    """
    fim = fim or date.today()
    inicio = fim - timedelta(days=JANELA_DIAS - 1)

    params = {
        "start_date": inicio.isoformat(),
        "end_date": fim.isoformat(),
        "api_key": os.getenv("NASA_API_KEY", "DEMO_KEY"),
    }

    sessao = _sessao_com_retry()
    try:
        resp = sessao.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Falha ao consultar a NASA NeoWs: {e}") from e

    dados = resp.json()
    linhas: list[dict] = []
    # near_earth_objects é um dict {data: [objetos...]} — juntamos todos os dias.
    for objetos_do_dia in dados.get("near_earth_objects", {}).values():
        for obj in objetos_do_dia:
            linha = _achatar_objeto(obj)
            if linha is not None:
                linhas.append(linha)

    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    return df.sort_values("distancia_lunar").reset_index(drop=True)


if __name__ == "__main__":
    df = coletar_semana()
    if df.empty:
        print("Nenhuma aproximação encontrada na janela.")
    else:
        print(f"Semana coletada: {len(df)} asteroides.")
        print(f"Perigosos (flag NASA): {int(df['perigoso_nasa'].sum())}")
        cols = ["nome", "diametro_m", "velocidade_kms", "distancia_lunar", "perigoso_nasa"]
        print(df[cols].head(10).to_string(index=False))
