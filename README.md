# 🛰️ Sentinela — Radar Semanal de Risco de Asteroides

Pipeline de IA que, toda semana, coleta as aproximações de asteroides à Terra na
**NASA NeoWs**, calcula um score de risco físico (baseline), pede a um **LLM** um resumo
executivo com **saída estruturada (Pydantic)**, avalia o resultado em três camadas e envia
o digest pelo **WhatsApp** — agendado no **GitHub Actions**.

Trabalho final da disciplina **AI Applications (MBA)** · metodologia **CRISP-DM** dirigindo
o **Claude Code**. Regra de ouro: **nenhum número é inventado** — todo valor vem de código
que roda sobre dados reais.

---

## Pré-requisitos

**Obrigatórios:**

- **Python ≥ 3.10** — [python.org/downloads](https://www.python.org/downloads/) (no Windows,
  marque *Add Python to PATH* na instalação)
- **Git** — [git-scm.com](https://git-scm.com)
- **Chave da NASA NeoWs** — grátis em [api.nasa.gov](https://api.nasa.gov)
  (ou use `DEMO_KEY`, com limite de requisições mais baixo)
- **Chave da OpenAI** — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  (paga por uso; custa centavos por execução). *Sem ela, rode no modo `--simular-llm`.*

**Opcionais:**

- **Quarto + TinyTeX** — para gerar o relatório em PDF e os slides:
  [quarto.org/docs/get-started](https://quarto.org/docs/get-started) e depois
  `quarto install tinytex`
- **Conta Meta (WhatsApp Cloud API)** — para o envio automático do digest (bônus):
  [developers.facebook.com](https://developers.facebook.com). Ver seção *WhatsApp* abaixo.

> Testado em Windows 11 com Python 3.14; funciona também em macOS e Linux
> (ajuste só o comando de ativação do `.venv`).

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

# 3. Pipeline completo (via CLI do pacote)
python -m sentinela --simular-llm --sem-envio   # dry-run OFFLINE (sem nenhuma chave)
python -m sentinela --sem-envio                 # com LLM real, sem enviar WhatsApp
python -m sentinela                             # tudo: coleta -> LLM -> WhatsApp
# (equivalente: python main.py [...] — atalho na raiz)

# 4. Testes
python -m pytest -q
```

> `pip install -r requirements.txt` instala o pacote `sentinela` em modo editável
> (deps no `pyproject.toml`) + os extras de relatório e testes.

> **Sem chave de LLM?** Use `--simular-llm`: um fallback determinístico monta o mesmo
> schema a partir dos dados (sem inventar números). Para a entrega, rode com a
> `OPENAI_API_KEY` de verdade e faça commit do `saidas/relatorio.json` gerado.

## Relatório (paper) e apresentação

Precisa do [Quarto](https://quarto.org) e, para PDF, de LaTeX (`quarto install tinytex`):

```bash
quarto render relatorio/paper.qmd --to pdf     # relatório técnico (as 6 fases do CRISP-DM)
quarto render relatorio/paper.qmd --to html    # versão rápida, sem LaTeX
quarto render relatorio/apresentacao.qmd       # slides executivos (reveal.js)
```

Os `.qmd` leem um *snapshot* real versionado em `dados/amostra_semana.csv`, então
**renderizam sem chave e sem rede** — todo número exibido sai de um chunk que roda.

## Estrutura (arquitetura limpa em camadas)

A dependência aponta sempre para dentro: **aplicação → infra → domínio**. O domínio
não conhece o mundo externo; a infra adapta serviços (NASA, OpenAI, WhatsApp); a
aplicação orquestra tudo recebendo os adaptadores por injeção (DIP).

```
src/sentinela/
├── dominio/          # regras de negócio puras (sem I/O)
│   ├── modelos.py    # entidades Pydantic (saída estruturada)
│   ├── risco.py      # baseline de score de risco (Fase 4)
│   └── avaliacao.py  # 3 camadas de avaliação (Fase 5)
├── infra/            # adaptadores externos (I/O)
│   ├── nasa.py       # coleta NeoWs (Fase 3)
│   ├── llm.py        # OpenAI GPT + structured output (Fase 4)
│   └── whatsapp.py   # Meta Cloud API (Fase 6)
├── aplicacao/
│   └── pipeline.py   # caso de uso: orquestra o pipeline (Fase 6)
└── __main__.py       # CLI (python -m sentinela)

relatorio/            # relatório e slides (Quarto)
├── paper.qmd         # relatório técnico → PDF
├── apresentacao.qmd  # slides executivos
├── referencias.bib   # bibliografia
└── fundo.html        # fundo estelar dos slides
```

| Fora do pacote | O que é |
|---|---|
| `main.py` | Atalho para a CLI (`python -m sentinela`) |
| `pyproject.toml` · `requirements.txt` | Empacotamento e dependências |
| `relatorio/` | Relatório técnico (PDF) e slides (Quarto) |
| `.github/workflows/semanal.yml` | Agendamento semanal (cron) |
| `dados/` · `assets/` · `entrega/` · `tests/` | Snapshot real · imagens · renderizados · testes |

## Avaliação em três camadas

1. **Baseline vs. flag oficial da NASA** — o `score_risco` como classificador da flag
   *potentially hazardous* (matriz de confusão, precisão, recall, F1, AUC).
2. **Concordância LLM × baseline** — os destaques do LLM são coerentes com o ranking de
   risco? (rank médio dos destaques, % no topo do baseline e % marcados como perigosos
   pela NASA).
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
