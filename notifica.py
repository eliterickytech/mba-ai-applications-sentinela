"""
notifica.py — Fase 6 (Implantação): envio do digest pela WhatsApp Cloud API (Meta).

Lê do .env: WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_DESTINO.
Faz POST na Graph API. Se o envio de texto livre falhar (janela de 24h fechada),
cai para um template aprovado (hello_world). Levanta erro claro em status != 200.

O texto é formatado a partir do schema RelatorioSemanal — a mensagem nasce da
saída estruturada, não de texto solto.
"""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

from schema import RelatorioSemanal

load_dotenv()

GRAPH_VERSION = "v25.0"


def formatar_mensagem(rel: RelatorioSemanal) -> str:
    """Converte o schema numa mensagem de WhatsApp legível (negrito com *asteriscos*)."""
    linhas = [f"*🛰️ {rel.titulo}*", f"_Nível da semana: {rel.nivel_semana}_", ""]
    linhas.append(rel.resumo_executivo)
    linhas.append("")
    for b in rel.bullets:
        linhas.append(f"• {b}")
    if rel.objetos_destaque:
        linhas.append("")
        linhas.append("*Objetos em destaque:*")
        for o in rel.objetos_destaque:
            linhas.append(
                f"• *{o.nome}* — {o.diametro_m:.0f} m, {o.distancia_lunar:.0f} dist. lunares "
                f"(score {o.score_risco:.0f}). {o.motivo}"
            )
    if rel.alerta:
        linhas.append("")
        linhas.append(f"⚠️ *Alerta:* {rel.alerta}")
    linhas.append("")
    linhas.append(f"_{rel.numero_destaque} · dados: NASA NeoWs_")
    return "\n".join(linhas)


def _payload_texto(destino: str, texto: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": destino,
        "type": "text",
        "text": {"body": texto},
    }


def _payload_template(destino: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": destino,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }


def enviar_mensagem(texto: str) -> dict:
    """Envia `texto` pelo WhatsApp. Retorna o JSON da API. Levanta erro se falhar."""
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    destino = os.getenv("WHATSAPP_DESTINO")
    if not all([token, phone_id, destino]):
        raise RuntimeError(
            "Configure WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_DESTINO no .env."
        )

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, json=_payload_texto(destino, texto), timeout=30)
    if resp.status_code == 200:
        return resp.json()

    # Janela de 24h fechada (ou texto livre bloqueado): cai para template aprovado.
    print(f"[whatsapp] texto livre falhou ({resp.status_code}); tentando template hello_world...")
    resp2 = requests.post(url, headers=headers, json=_payload_template(destino), timeout=30)
    if resp2.status_code == 200:
        return resp2.json()

    raise RuntimeError(
        f"Falha ao enviar WhatsApp. texto={resp.status_code} {resp.text[:200]} | "
        f"template={resp2.status_code} {resp2.text[:200]}"
    )
