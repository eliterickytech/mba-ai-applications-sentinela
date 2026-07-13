# 🛰️ Sentinela — Radar Semanal de Risco de Asteroides

Pipeline de IA que, toda semana, coleta as aproximações de asteroides à Terra na
**NASA NeoWs**, calcula um score de risco físico (baseline), pede a um **LLM (OpenAI GPT)**
um resumo executivo com **saída estruturada (Pydantic)**, avalia o resultado em três
camadas e envia o digest pelo **WhatsApp** — agendado no **GitHub Actions**.

Trabalho final da disciplina **AI Applications (MBA)** · metodologia **CRISP-DM** dirigindo
o **Claude Code**. Regra de ouro: **nenhum número é inventado** — todo valor vem de código
que roda sobre dados reais.

---

## 1. Pré-requisitos

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
  [developers.facebook.com](https://developers.facebook.com). Ver seção 6.

> Testado em Windows 11 com Python 3.14; funciona também em macOS e Linux
> (ajuste só o comando de ativação do `.venv`).

---

## 2. Passo a passo de execução

```bash
# 1. Clonar o repositório
git clone https://github.com/eliterickytech/mba-ai-applications-sentinela.git
cd mba-ai-applications-sentinela

# 2. Criar e ativar o ambiente virtual isolado
python -m venv .venv
source .venv/Scripts/activate        # Windows: .venv\Scripts\activate
                                     # macOS/Linux: source .venv/bin/activate

# 3. Instalar tudo (pacote + dependências, definidas no pyproject.toml)
pip install -r requirements.txt

# 4. Configurar as chaves
cp .env.example .env                 # depois edite o .env e preencha:
#   NASA_API_KEY    -> sua chave grátis (ou DEMO_KEY)
#   OPENAI_API_KEY  -> necessária para o LLM real (senão use --simular-llm)
#   WHATSAPP_*      -> opcional; só para o envio (ver seção 6)

# 5. Rodar o pipeline (escolha um modo)
python -m sentinela --simular-llm --sem-envio   # dry-run OFFLINE (sem nenhuma chave)
python -m sentinela --sem-envio                 # com LLM real, sem enviar WhatsApp
python -m sentinela                             # completo: coleta -> LLM -> WhatsApp
#   (equivale a: python main.py [...] — atalho na raiz)

# 6. Rodar os testes
python -m pytest -q

# 7. (Opcional) Gerar o relatório PDF e os slides — precisa do Quarto + TinyTeX
quarto render relatorio/paper.qmd --to pdf      # relatório técnico (6 fases do CRISP-DM)
quarto render relatorio/apresentacao.qmd        # slides executivos (reveal.js)
```

> **O que cada modo faz:** `--simular-llm` troca o GPT por um resumo determinístico montado
> a partir dos próprios dados (sem inventar números) — útil sem chave/CI. `--sem-envio` gera
> todos os artefatos mas não dispara o WhatsApp.

---

## 3. Onde encontrar a informação gerada

**A cada execução** o pipeline grava em **`saidas/`** (pasta local, fora do git):

| Arquivo | O que contém |
|---|---|
| `saidas/amostra_semana.csv` | A semana coletada da NASA, já com o score de risco de cada asteroide |
| `saidas/relatorio.json` | A **saída estruturada do LLM** (título, bullets, objetos de destaque, alerta) |
| `saidas/avaliacao.json` | As métricas das **3 camadas** (F1, AUC, concordância, auditoria da regra de ouro) |
| `saidas/mensagem.txt` | A mensagem exatamente como foi formatada e enviada ao WhatsApp |

**Entregáveis renderizados** (versionados) ficam em **`entrega/`**:

| Arquivo | O que é |
|---|---|
| `entrega/paper.pdf` | Relatório técnico final (as 6 fases do CRISP-DM) |
| `entrega/apresentacao.html` | Slides executivos (abra no navegador) |

**No WhatsApp:** se rodar sem `--sem-envio`, o digest chega no número configurado em
`WHATSAPP_DESTINO`.

> Os arquivos em `dados/` são um *snapshot real* de referência (uma semana já capturada da
> NASA + saída do GPT), usado pelo relatório para renderizar sem precisar de chave nem rede.

---

## 4. Estrutura completa do projeto

```
sentinela/
│
├── src/sentinela/            # 🧩 O CÓDIGO — arquitetura limpa em camadas
│   ├── __init__.py           # define o pacote e sua versão
│   ├── __main__.py           # CLI: implementa `python -m sentinela`
│   │
│   ├── dominio/              # 🧠 regras de negócio puras (sem I/O externo)
│   │   ├── modelos.py        # entidades Pydantic (o schema da saída estruturada)
│   │   ├── risco.py          # baseline: score de risco físico 0–100 (Fase 4)
│   │   └── avaliacao.py      # as 3 camadas de avaliação (Fase 5)
│   │
│   ├── infra/               # 🔌 adaptadores de serviços externos (I/O)
│   │   ├── nasa.py           # coleta na NASA NeoWs, com retry/backoff (Fase 3)
│   │   ├── llm.py            # OpenAI GPT + structured output (Fase 4)
│   │   └── whatsapp.py       # envio pela Meta WhatsApp Cloud API (Fase 6)
│   │
│   └── aplicacao/           # 🎯 orquestração
│       └── pipeline.py       # o caso de uso: junta as camadas (com injeção de deps)
│
├── relatorio/               # 📄 relatório e slides (Quarto)
│   ├── paper.qmd             # fonte do relatório técnico → PDF
│   ├── apresentacao.qmd      # fonte dos slides executivos
│   ├── referencias.bib       # bibliografia (BibTeX)
│   └── fundo.html            # fundo estelar dos slides (imagem embutida)
│
├── dados/                   # 📦 snapshot real (lido pelo relatório)
│   ├── amostra_semana.csv    # uma semana capturada da NASA (com score)
│   ├── relatorio_exemplo.json# a saída estruturada real do GPT para essa semana
│   └── relatorio_meta.json   # proveniência do exemplo acima
│
├── assets/                  # 🎨 imagens e seus geradores
│   ├── logo.png              # logo do projeto
│   ├── earth-nasa.jpg        # Terra (NASA Blue Marble, domínio público)
│   ├── fundo-slides.png      # fundo dos slides (gerado)
│   ├── gerar_logo.py         # script que cria o logo
│   └── gerar_fundo_slides.py # script que cria o fundo dos slides
│
├── entrega/                 # ✅ entregáveis renderizados (versionados)
│   ├── paper.pdf             # relatório técnico final
│   └── apresentacao.html     # slides executivos
│
├── tests/                   # 🧪 testes
│   └── test_pipeline.py      # parsing, score, métricas, regra de ouro, pipeline
│
├── .github/workflows/
│   └── semanal.yml           # agendamento semanal na nuvem (cron)
│
├── main.py                   # atalho da CLI (equivale a `python -m sentinela`)
├── pyproject.toml            # empacotamento e dependências (fica na raiz por convenção)
├── requirements.txt          # instala o pacote + extras num comando
├── CLAUDE.md                 # briefing do projeto e a regra de ouro
├── README.md                 # este arquivo
├── .gitignore                # o que não vai para o git (inclui .env e saidas/)
└── .env.example              # modelo das chaves (copie para .env e preencha)
```

**Não versionados** (criados localmente): `.venv/` (ambiente), `.env` (suas chaves) e
`saidas/` (resultados de cada execução).

---

## 5. Arquitetura e avaliação

**Camadas (dependência aponta para dentro):** `aplicação → infra → domínio`. O domínio não
conhece NASA, OpenAI nem WhatsApp; a infra adapta esses serviços; a aplicação orquestra
recebendo os adaptadores por **injeção de dependência** (DIP). Trocar o LLM ou o canal de
envio mexe só na pasta `infra/`.

**Avaliação em três camadas** (`dominio/avaliacao.py`):

1. **Baseline vs. flag oficial da NASA** — o `score_risco` como classificador da flag
   *potentially hazardous* (matriz de confusão, precisão, recall, F1, AUC).
2. **Concordância LLM × baseline** — os destaques do LLM são coerentes com o ranking de
   risco? (rank médio, % no topo do baseline e % marcados como perigosos pela NASA).
3. **Auditoria da regra de ouro** — todo número citado pelo LLM existe mesmo nos dados?
   (checagem programática; um teste garante que um número inventado seria detectado).

---

## 6. WhatsApp (bônus — automação real)

1. Crie um app *Business* em [developers.facebook.com](https://developers.facebook.com) e
   adicione o produto **WhatsApp**.
2. Em *API Setup*, pegue o **token**, o **Phone number ID** e cadastre o número que vai
   receber (na conta de teste, só entrega para números cadastrados).
3. Preencha `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` e `WHATSAPP_DESTINO` no `.env`.
4. Para a automação na nuvem, cadastre os mesmos valores + `NASA_API_KEY` e `OPENAI_API_KEY`
   em *Settings → Secrets and variables → Actions* do repositório. O workflow
   `.github/workflows/semanal.yml` roda toda segunda às 8h (Brasília).

> O token de teste da Meta é temporário (~24h). Para o agendamento rodar sozinho, gere um
> token permanente (System User no Business Manager).

---

## 7. Segurança e fonte de dados

- **Segredos** ficam **só** no `.env` (que está no `.gitignore`) ou nos *Secrets* do GitHub.
  Nunca no código, nunca no commit.
- **Fonte:** NASA NeoWs — Near Earth Object Web Service · <https://api.nasa.gov>
