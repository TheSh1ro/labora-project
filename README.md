# Agente Q&A de Direito Laboral Portugues

Agente conversacional pronto para producao que responde a questoes sobre direito laboral e processamento salarial portugues, usando pesquisa web em tempo real e tool calling estruturado.

> Desenvolvido para o **HomoDeus AI Engineer Challenge 2025**

## Funcionalidades

- **Camada de Retrieval**: Pesquisa web em fontes oficiais portuguesas (Portal das Financas, CITE, DRE, Codigo do Trabalho)
- **Agente Conversacional**: Interface Q&A multi-turno com arquitetura de tool calling
- **Suite de Avaliacao**: Harness de avaliacao com 12 casos de teste e metricas de qualidade
- **Citacoes de Fontes**: Cada resposta inclui URLs das fontes consultadas
- **Calculos Especializados**: Subsidios, TSU, IRS com formulas e passo a passo

## Quick Start

### Pre-requisitos

- Node.js 20+
- Python 3.9+
- API Keys: Groq e Tavily

### Modelo LLM

O agente usa o modelo **`llama-3.3-70b-versatile`** via [Groq API](https://groq.com), com suporte a tool calling nativo.

### 1. Clone e Instale

```bash
git clone <repository-url>
cd homodeus-app-v1
```

### 2. Configure as Variaveis de Ambiente

```bash
# Backend
cp backend/.env.example backend/.env
# Edite backend/.env com suas API keys (GROQ_API_KEY e TAVILY_API_KEY)

# Frontend
cp .env.example .env
# Edite .env se necessario (padrao: http://localhost:8000)
```

### 3. Instale as Dependencias

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (em outro terminal)
cd ..
npm install
```

### 4. Execute

```bash
# Backend (porta 8000)
cd backend
uvicorn app.main:app --reload

# Frontend (em outro terminal, porta 5173)
npm run dev
```

### 5. Acesse

- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat Interface│  │ Evaluation   │  │ Sources Panel        │  │
│  │              │  │ Dashboard    │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Agente Conversacional                      │    │
│  │         (Groq / LLaMA 3.3 70B / Tool Calling)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│        ┌─────────────────────┼─────────────────────┐             │
│        ▼                     ▼                     ▼             │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐         │
│  │  search_ │         │ calculate│         │  extract_│         │
│  │  labor_  │         │  subsidy │         │  irs_    │         │
│  │  law     │         │          │         │  rates   │         │
│  └──────────┘         └──────────┘         └──────────┘         │
│        │                     │                     │             │
│        └─────────────────────┼─────────────────────┘             │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   Tavily API    │                          │
│                    │  (Web Search)   │                          │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Tools Disponiveis

| Tool | Descricao | Fontes |
|------|-----------|--------|
| `search_labor_law` | Pesquisa no Codigo do Trabalho | portal.act.gov.pt |
| `search_irs_tables` | Consulta tabelas de retencao IRS | info.portaldasfinancas.gov.pt |
| `search_social_security` | Pesquisa TSU e contribuicoes | diariodarepublica.pt |
| `calculate_vacation_subsidy` | Calcula subsidio de ferias | - |
| `calculate_christmas_subsidy` | Calcula subsidio de Natal | - |
| `get_minimum_wage` | Retorna salario minimo nacional | - |
| `calculate_tsu` | Calcula contribuicoes TSU | - |

## Suite de Avaliacao

### Metricas

| Metrica | Descricao | Peso |
|---------|-----------|------|
| Correctness | Resposta factualmente correta | 40% |
| Citation Quality | Fontes citadas e relevantes | 30% |
| Graceful Refusal | Recusa apropriada quando nao sabe | 20% |
| Response Time | Tempo de resposta < 10s | 10% |

### Casos de Teste (12)

| ID | Categoria | Pergunta |
|----|-----------|----------|
| basic_001 | Basico | Qual e o salario minimo nacional atual? |
| basic_002 | Basico | A quantos dias de ferias tenho direito? |
| intermediate_001 | Intermedio | Como calcular subsidio de ferias para 1500€? |
| intermediate_002 | Intermedio | Quais as taxas TSU? |
| intermediate_003 | Intermedio | Prazo de aviso previo para 3 anos? |
| advanced_001 | Avancado | Calculo proporcional do subsidio de Natal |
| advanced_002 | Avancado | Taxas IRS para solteiro com 2200€ |
| advanced_003 | Avancado | Condicoes para lay-off |
| limit_001 | Limite | Teletrabalho de Espanha |
| limit_002 | Limite | Clausula de nao concorrencia de 3 anos |
| extra_001 | Intermedio | Subsidio de Natal para trabalhador contratado em julho com 2000€ |
| extra_002 | Intermedio | Valor liquido de trabalhador com 1800€ brutos |

## Exemplos de Perguntas

```
"Qual e o salario minimo nacional atual em Portugal?"
"A quantos dias de ferias tem direito um trabalhador a tempo inteiro?"
"Como se calcula o subsidio de ferias para um trabalhador que ganha 1.500 EUR/mes?"
"Quais sao as taxas de contribuicao TSU do empregador e do trabalhador?"
"Que prazo de aviso previo e necessario para despedir um trabalhador com 3 anos de antiguidade?"
"Quais as taxas de retencao na fonte de IRS para um contribuinte solteiro com 2.200 EUR brutos/mes?"
```

## API Endpoints

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/` | GET | Health check |
| `/health` | GET | Health check detalhado |
| `/chat` | POST | Enviar mensagem |
| `/chat/stream` | POST | Enviar mensagem com streaming |
| `/evaluation/cases` | GET | Listar casos de teste |
| `/evaluation/run` | POST | Executar avaliacao |
| `/agent/info` | GET | Informacoes sobre o agente e modelo |
| `/agent/usage` | GET | Consumo acumulado de tokens e custo estimado |
| `/agent/usage` | DELETE | Reiniciar contadores de tokens |
| `/tools` | GET | Listar tools disponiveis |
| `/sources` | GET | Listar fontes oficiais |

## Decisoes de Arquitetura

1. **Tool Calling vs Prompting**: Arquitetura de tool calling estruturada em vez de prompting de turno unico para maior controlo, rastreabilidade e testabilidade.

2. **Groq + LLaMA 3.3 70B**: Uso da Groq API com o modelo `llama-3.3-70b-versatile` para inferencia rapida com suporte nativo a tool calling.

3. **Fontes Oficiais**: Integracao com Tavily API para pesquisa em dominios oficiais portugueses, garantindo factualidade.

4. **Calculos Localizados**: Formulas de calculo implementadas localmente para garantir precisao matematica.

5. **Avaliacao Automatizada**: Suite de avaliacao com metricas quantitativas para medir qualidade do agente.

## Estrutura do Projeto

```
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── tools.py
│   │   ├── models.py
│   │   └── evaluation.py
│   ├── requirements.txt
│   └── .env.example
├── src/
│   ├── components/
│   │   ├── Chat.tsx
│   │   ├── Message.tsx
│   │   ├── ToolCall.tsx
│   │   ├── SourcesPanel.tsx
│   │   └── EvaluationDashboard.tsx
│   ├── hooks/
│   │   └── useChat.ts
│   └── types/
│       └── index.ts
├── package.json
└── README.md
```

## Licenca

MIT License - Desenvolvido para o HomoDeus Challenge 2025.

---

**Nota**: Este agente e um demonstrador tecnico. Para aconselhamento juridico especifico, consulte um advogado especializado.