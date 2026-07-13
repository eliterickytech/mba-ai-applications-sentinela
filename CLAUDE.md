# Sentinela — Radar Semanal de Risco de Asteroides

**Disciplina:** AI Applications — MBA · **Metodologia:** CRISP-DM dirigindo o Claude Code.

## Objetivo (Entendimento do Negócio)

Todo asteroide catalogado que passa perto da Terra é registrado pela NASA. São dezenas
por semana. Um núcleo de **divulgação científica / defesa planetária** não tem tempo de
ler a lista crua: precisa de um resumo executivo que responda **"o que merece atenção
esta semana?"**.

O **Sentinela** é um pipeline que, toda semana, coleta as aproximações da semana,
calcula um score de risco físico, pede a um LLM um resumo estruturado e prioriza os
objetos de destaque — entregando um digest pronto para decisão.

**Decisão que muda:** para onde o núcleo direciona atenção/comunicação na semana.
**Métrica de sucesso:** o ranking de risco (baseline + LLM) concorda com a
classificação oficial da NASA (`is_potentially_hazardous_asteroid`).

## Fonte de dados

- **NASA NeoWs (Near Earth Object Web Service)** — API pública e gratuita.
  Endpoint `feed`: aproximações num intervalo de até 7 dias.
  `https://api.nasa.gov/neo/rest/v1/feed?start_date=...&end_date=...&api_key=...`
- Campos usados (todos reais, vindos da API): `name`, `absolute_magnitude_h`,
  `estimated_diameter.meters`, `is_potentially_hazardous_asteroid`, `is_sentry_object`,
  e por aproximação: `close_approach_date_full`, `relative_velocity.kilometers_per_second`,
  `miss_distance.lunar` e `.kilometers`.

## Arquitetura (camadas — dependência aponta para dentro)

Aplicação → Infra → Domínio. Ver `src/sentinela/`:

- `dominio/modelos.py` — entidades Pydantic (saída estruturada).
- `dominio/risco.py` — baseline de risco físico (tamanho, velocidade, distância).
- `dominio/avaliacao.py` — 3 camadas de avaliação (vs. NASA, concordância, regra de ouro).
- `infra/nasa.py` — NeoWs → DataFrame limpo (retry + backoff).
- `infra/llm.py` — LLM (OpenAI/GPT) com structured output.
- `infra/whatsapp.py` — envio pela WhatsApp Cloud API (Meta).
- `aplicacao/pipeline.py` — orquestra coleta → score → resumo → avaliação → notifica (com DIP).
- `__main__.py` / `main.py` — CLI (`python -m sentinela`).
- `relatorio/paper.qmd` — relatório Quarto (as 6 fases; números só via código).

## REGRA DE OURO (inegociável)

**Nenhum número é inventado.** Todo valor citado no digest, no paper ou na
apresentação vem de uma célula/execução que rodou sobre os dados reais da NASA.
Se um número não veio de algo executado, ele não entra.

## Convenções

- Ciclo `explore → plan → code → commit`.
- Segredos **só** no `.env` (que está no `.gitignore`) ou nos Secrets do GitHub.
  Nunca no código, nunca no commit.
- Saída do LLM sempre com **schema fixo (Pydantic)** — comparabilidade e confiança.
- Código comentado em português.
