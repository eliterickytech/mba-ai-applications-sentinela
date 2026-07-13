# 🛰️ Sentinela — Radar Semanal de Risco de Asteroides

Pipeline de IA que, toda semana, coleta as aproximações de asteroides à Terra na
**NASA NeoWs**, calcula um score de risco físico (baseline), pede a um **LLM** um resumo
executivo com **saída estruturada (Pydantic)**, avalia o resultado em três camadas e envia
o digest pelo **WhatsApp** — agendado no **GitHub Actions**.

Trabalho final da disciplina **AI Applications (MBA)** · metodologia **CRISP-DM** dirigindo
o **Claude Code**. Regra de ouro: **nenhum número é inventado** — todo valor vem de código
que roda sobre dados reais.

---

## Como rodar do zero

```bash
# 1. Ambiente isolado
python -m venv .venv
source .venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Chaves (copie e preencha)
cp .env.example .env
#   NASA_API_KEY   -> funciona com DEMO_KEY; sua chave grátis em api.nasa.gov
#   OPENAI_API_KEY -> platform.openai.com/api-keys  (necessária para o LLM real)
#   WHATSAPP_*     -> developers.facebook.com (opcional; ver seção WhatsApp)

# 3. Rodar cada etapa isoladamente
python coleta.py        # coleta a semana da NASA
python score.py         # baseline de risco físico
python avaliacao.py     # métricas baseline x flag oficial da NASA

# 4. Pipeline completo
python main.py --simular-llm --sem-envio   # dry-run OFFLINE (sem nenhuma chave)
python main.py --sem-envio                 # com LLM real, sem enviar WhatsApp
python main.py                             # tudo: coleta -> LLM -> WhatsApp

# 5. Testes
python -m pytest -q
```

> **Sem chave de LLM?** Use `--simular-llm`: um fallback determinístico monta o mesmo
> schema a partir dos dados (sem inventar números). Para a entrega, rode com a
> `OPENAI_API_KEY` de verdade e faça commit do `saidas/relatorio.json` gerado.

## Relatório (paper) e apresentação

Precisa do [Quarto](https://quarto.org) e, para PDF, de LaTeX (`quarto install tinytex`):

```bash
quarto render paper.qmd --to pdf          # relatório técnico (as 6 fases do CRISP-DM)
quarto render paper.qmd --to html         # versão rápida, sem LaTeX
quarto render apresentacao.qmd            # slides executivos (reveal.js)
```

Os `.qmd` leem um *snapshot* real versionado em `dados/amostra_semana.csv`, então
**renderizam sem chave e sem rede** — todo número exibido sai de um chunk que roda.

## Estrutura

| Arquivo | Fase CRISP-DM | O que faz |
|---|---|---|
| `coleta.py` | Preparação | NASA NeoWs → DataFrame limpo (retry + backoff) |
| `score.py` | Modelagem (baseline) | Score de risco físico 0–100 |
| `schema.py` | Modelagem | Contratos Pydantic (saída estruturada) |
| `resumo.py` | Modelagem (LLM) | OpenAI GPT + structured output |
| `avaliacao.py` | Avaliação | 3 camadas: vs. NASA, concordância, regra de ouro |
| `notifica.py` | Implantação | WhatsApp Cloud API |
| `main.py` | Implantação | Orquestra o pipeline |
| `paper.qmd` | — | Relatório técnico (Quarto → PDF) |
| `apresentacao.qmd` | — | Slides executivos |
| `.github/workflows/semanal.yml` | Implantação | Agendamento semanal (cron) |
| `tests/` | — | Testes (parsing, score, métricas, regra de ouro) |

## Avaliação em três camadas

1. **Baseline vs. flag oficial da NASA** — o `score_risco` como classificador da flag
   *potentially hazardous* (matriz de confusão, precisão, recall, F1, AUC).
2. **Concordância LLM × baseline** — os destaques do LLM coincidem com o topo do ranking
   físico? (Jaccard).
3. **Auditoria da regra de ouro** — todo número citado pelo LLM existe mesmo nos dados?
   (checagem programática; um teste garante que um número inventado é detectado).

## WhatsApp (bônus — automação real)

1. Crie um app *Business* em [developers.facebook.com](https://developers.facebook.com) e
   adicione o produto **WhatsApp**.
2. Em *API Setup*, pegue `Phone number ID` e o token de teste, e cadastre seu número.
3. Preencha `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` e `WHATSAPP_DESTINO` no `.env`.
4. Na nuvem, cadastre os mesmos valores em *Settings → Secrets and variables → Actions*.

## Segurança

Chaves ficam **só** no `.env` (que está no `.gitignore`) ou nos *Secrets* do GitHub.
Nunca no código, nunca no commit.

## Fonte de dados

NASA NeoWs — Near Earth Object Web Service · <https://api.nasa.gov>
