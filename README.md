# 🤖 Agente Q&A de Direito Laboral Português

Agente conversacional pronto para produção que responde a questões sobre direito laboral e processamento salarial português, usando pesquisa web em tempo real e tool calling estruturado.

> 🏆 Desenvolvido para o **HomoDeus AI Engineer Challenge 2025**

## ✨ Funcionalidades

- **🔍 Camada de Retrieval**: Pesquisa web em fontes oficiais portuguesas (Portal das Finanças, CITE, DRE, Código do Trabalho)
- **💬 Agente Conversacional**: Interface Q&A multi-turno com arquitetura de tool calling
- **📊 Suite de Avaliação**: Harness de avaliação com 10+ casos de teste e métricas de qualidade
- **📚 Citações de Fontes**: Cada resposta inclui URLs das fontes consultadas
- **🧮 Cálculos Especializados**: Subsídios, TSU, IRS com fórmulas e passo a passo

## 🚀 Quick Start

### Pré-requisitos

- Node.js 18+
- Python 3.9+
- API Keys: Groq e Tavily

### Modelo LLM

O agente usa o modelo **`llama-3.3-70b-versatile`** via [Groq API](https://groq.com), com suporte a tool calling nativo.

### 1. Clone e Instale

```bash
git clone <repository-url>
cd agente-direito-laboral-pt
```

### 2. Configure as Variáveis de Ambiente

```bash
# Backend
cp backend/.env.example backend/.env
# Edite backend/.env com suas API keys (GROQ_API_KEY e TAVILY_API_KEY)

# Frontend
cp .env.example .env
# Edite .env se necessário (padrão: http://localhost:8000)
```

### 3. Instale as Dependências

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

## 🏗️ Arquitetura

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
│  │         (Groq / Tool Calling)                          │    │
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

## 🛠️ Tools Disponíveis

| Tool | Descrição | Fontes |
|------|-----------|--------|
| `search_labor_law` | Pesquisa no Código do Trabalho | portal.act.gov.pt |
| `search_irs_tables` | Consulta tabelas de retenção IRS | info.portaldasfinancas.gov.pt |
| `search_social_security` | Pesquisa TSU e contribuições | diariodarepublica.pt |
| `calculate_vacation_subsidy` | Calcula subsídio de férias | - |
| `calculate_christmas_subsidy` | Calcula subsídio de Natal | - |
| `get_minimum_wage` | Retorna salário mínimo nacional | - |
| `calculate_tsu` | Calcula contribuições TSU | - |

## 📊 Suite de Avaliação

### Métricas

| Métrica | Descrição | Peso |
|---------|-----------|------|
| Correctness | Resposta factualmente correta | 40% |
| Citation Quality | Fontes citadas e relevantes | 30% |
| Graceful Refusal | Recusa apropriada quando não sabe | 20% |
| Response Time | Tempo de resposta < 10s | 10% |

### Casos de Teste

- **Básico**: Salário mínimo, dias de férias
- **Intermédio**: Cálculo de subsídios, taxas TSU, aviso prévio
- **Avançado**: IRS, lay-off, cálculos proporcionais
- **Limite**: Teletrabalho internacional, cláusulas de não concorrência

## 📝 Exemplos de Perguntas

```
✅ "Qual é o salário mínimo nacional atual em Portugal?"
✅ "A quantos dias de férias tem direito um trabalhador a tempo inteiro?"
✅ "Como se calcula o subsídio de férias para um trabalhador que ganha 1.500 EUR/mês?"
✅ "Quais são as taxas de contribuição TSU do empregador e do trabalhador?"
✅ "Que prazo de aviso prévio é necessário para despedir um trabalhador com 3 anos de antiguidade?"
✅ "Quais as taxas de retenção na fonte de IRS para um contribuinte solteiro com 2.200 EUR brutos/mês?"
```

## 🔌 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Health check |
| `/chat` | POST | Enviar mensagem |
| `/evaluation/cases` | GET | Listar casos de teste |
| `/evaluation/run` | POST | Executar avaliação |
| `/tools` | GET | Listar tools disponíveis |
| `/sources` | GET | Listar fontes oficiais |

## 🧪 Executar Testes

```bash
cd backend
pytest
```

## 📁 Estrutura do Projeto

```
.
├── backend/              # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py      # Entry point
│   │   ├── agent.py     # Agente conversacional
│   │   ├── tools.py     # Tool definitions
│   │   ├── models.py    # Pydantic models
│   │   └── evaluation.py # Suite de avaliação
│   ├── requirements.txt
│   └── .env.example
├── src/                  # React Frontend
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

## 🎯 Decisões de Arquitetura

1. **Tool Calling vs Prompting**: Escolhi arquitetura de tool calling estruturada em vez de prompting de turno único para maior controle e precisão.

2. **Groq + LLaMA 3.3 70B**: Uso da Groq API com o modelo `llama-3.3-70b-versatile` para inferência rápida com suporte nativo a tool calling, substituindo a OpenAI.

3. **Fontes Oficiais**: Integração com Tavily API para pesquisa em domínios oficiais portugueses, garantindo factualidade.

3. **Cálculos Localizados**: Fórmulas de cálculo implementadas localmente para garantir precisão matemática.

4. **Avaliação Automatizada**: Suite de avaliação com métricas quantitativas para medir qualidade do agente.

## 📄 Licença

MIT License - Desenvolvido para o HomoDeus Challenge 2025.

---

**Nota**: Este agente é um demonstrador técnico. Para aconselhamento jurídico específico, consulte um advogado especializado.